import torch
import torch.nn as nn
import numpy as np
from utilities.util import *
from models.model import Model
from learning_algorithms.ddpg import *
from collections import namedtuple
import torch.nn.functional as F




class M3DDPG(Model):

    def __init__(self, args, target_net=None):
        super(M3DDPG, self).__init__(args)
        self.construct_model()
        self.apply(self.init_weights)
        if target_net != None:
            self.target_net = target_net
            self.reload_params_to_target()
        self.Transition = namedtuple('Transition', ('state', 'action', 'reward', 'next_state', 'done', 'last_step'))

        self.num_adversaries = args.num_adversaries
        self.use_m3ddpg_good = args.use_m3ddpg_good
        self.use_m3ddpg_bad = args.use_m3ddpg_bad
        self.adv_eps = args.adv_eps
        self.adv_eps_s = args.adv_eps_s

    def construct_policy_net(self):
        # TODO: fix policy params update
        action_dicts = []
        if self.args.shared_parameters:
            l1 = nn.Linear(self.obs_dim, self.hid_dim)
            l2 = nn.Linear(self.hid_dim, self.hid_dim)
            a = nn.Linear(self.hid_dim, self.act_dim)
            for i in range(self.n_):
                action_dicts.append(nn.ModuleDict( {'layer_1': l1,\
                                                    'layer_2': l2,\
                                                    'action_head': a
                                                    }
                                                 )
                                   )
        else:
            for i in range(self.n_):
                action_dicts.append(nn.ModuleDict( {'layer_1': nn.Linear(self.obs_dim, self.hid_dim),\
                                                    'layer_2': nn.Linear(self.hid_dim, self.hid_dim),\
                                                    'action_head': nn.Linear(self.hid_dim, self.act_dim)
                                                    }
                                                  )
                                   )
        self.action_dicts = nn.ModuleList(action_dicts)

    def construct_value_net(self):
        # TODO: policy params update
        value_dicts = []
        if self.args.shared_parameters:
            l1 = nn.Linear( (self.obs_dim+self.act_dim)*self.n_, self.hid_dim )
            l2 = nn.Linear(self.hid_dim, self.hid_dim)
            v = nn.Linear(self.hid_dim, 1)
            for i in range(self.n_):
                value_dicts.append(nn.ModuleDict( {'layer_1': l1,\
                                                   'layer_2': l2,\
                                                   'value_head': v
                                                  }
                                                )
                                  )
        else:
            for i in range(self.n_):
                value_dicts.append(nn.ModuleDict( {'layer_1': nn.Linear( (self.obs_dim+self.act_dim)*self.n_, self.hid_dim ),\
                                                   'layer_2': nn.Linear(self.hid_dim, self.hid_dim),\
                                                   'value_head': nn.Linear(self.hid_dim, 1)
                                                  }
                                                )
                                  )
        self.value_dicts = nn.ModuleList(value_dicts)

    def construct_model(self):
        self.construct_value_net()
        self.construct_policy_net()

    def policy(self, obs, schedule=None, last_act=None, last_hid=None, info={}, stat={}):
        # TODO: policy params update
        actions = []
        for i in range(self.n_):
            h = torch.relu( self.action_dicts[i]['layer_1'](obs[:, i, :]) )
            h = torch.relu( self.action_dicts[i]['layer_2'](h) )
            a = self.action_dicts[i]['action_head'](h)
            actions.append(a)
        actions = torch.stack(actions, dim=1)
        return actions

    def get_adversarial_value(self, obs, act, i):
        batch_size = len(obs)
        if i < self.num_adversaries:
            adv_rate = [self.adv_eps_s *(i < self.num_adversaries) + self.adv_eps * (i >= self.num_adversaries) for i in range(self.n_)]
        else:
            adv_rate = [self.adv_eps_s *(i >= self.num_adversaries) + self.adv_eps * (i < self.num_adversaries) for i in range(self.n_)]
        adv_rate[i] = 0.0
        adv_rate = cuda_wrapper(torch.tensor(adv_rate), self.cuda_)

        differentiable_act = torch.nn.Parameter(act.clone(), requires_grad=True)
        pg_loss = -(self.get_normal_value(obs, differentiable_act, i)).mean()

        # external_grad = torch.ones(1,len(differentiable_act))
        # pg_loss.backward(gradient=external_grad)
        pg_loss.backward()
        perturb = (F.normalize(differentiable_act.grad, dim=1, p=2) * adv_rate[None,:,None]).detach()

        new_action = act + perturb
        return self.get_normal_value(obs, new_action, i)

    def get_normal_value(self, obs, act, i):
        h = torch.relu( self.value_dicts[i]['layer_1']( torch.cat( ( obs.contiguous().view( -1, np.prod(obs.size()[1:]) ), act.contiguous().view( -1, np.prod(act.size()[1:]) ) ), dim=-1 ) ) )
        h = torch.relu( self.value_dicts[i]['layer_2'](h) )
        return self.value_dicts[i]['value_head'](h)

    def value(self, obs, act):
        # TODO: policy params update
        values = []
        for i in range(self.n_):
            if (i < self.num_adversaries and self.use_m3ddpg_bad) or (i >= self.num_adversaries and self.use_m3ddpg_good):
                v = self.get_adversarial_value(obs, act, i)
            else:
                v = self.get_normal_value(obs, act, i)
            values.append(v)
                
        values = torch.stack(values, dim=1)
        return values

    def get_loss(self, batch):
        # TODO: fix policy params update
        batch_size = len(batch.state)
        # collect the transition data
        rewards, last_step, done, actions, state, next_state = self.unpack_data(batch)
        # construct the computational graph
        # do the argmax action on the action loss
        action_out = self.policy(state)
        actions_ = select_action(self.args, action_out, status='train', exploration=False)
        values_ = self.value(state, actions_).contiguous().view(-1, self.n_)
        # do the exploration action on the value loss
        values = self.value(state, actions).contiguous().view(-1, self.n_)
        # do the argmax action on the next value loss
        next_action_out = self.target_net.policy(next_state)
        next_actions_ = select_action(self.args, next_action_out, status='train', exploration=False)
        next_values_ = self.target_net.value(next_state, next_actions_.detach()).contiguous().view(-1, self.n_)
        returns = cuda_wrapper(torch.zeros((batch_size, self.n_), dtype=torch.float), self.cuda_)
        assert values_.size() == next_values_.size()
        assert returns.size() == values.size()
        for i in reversed(range(rewards.size(0))):
            if last_step[i]:
                next_return = 0 if done[i] else next_values_[i].detach()
            else:
                next_return = next_values_[i].detach()
            returns[i] = rewards[i] + self.args.gamma * next_return
        deltas = returns - values
        advantages = values_
        # advantages = advantages.contiguous().view(-1, 1)
        if self.args.normalize_advantages:
            advantages = batchnorm(advantages)
        action_loss = -advantages
        action_loss = action_loss.mean(dim=0)
        value_loss = deltas.pow(2).mean(dim=0)
        return action_loss, value_loss, action_out
