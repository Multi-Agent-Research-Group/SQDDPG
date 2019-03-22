from multiagent.environment import MultiAgentEnv
import multiagent.scenarios as scenario
import numpy as np
from commnet import *
from trainer import *
from gym_wrapper import *
import torch
from collections import namedtuple


scenario_name = 'simple_spread'
# scenario_name = 'simple_world_comm'
# scenario_name = 'simple'

# load scenario from script
scenario = scenario.load(scenario_name + ".py").Scenario()
# create world
world = scenario.make_world()
# create multiagent environment
env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation, info_callback=None, shared_viewer=True)

env.mode = 'human'

env = GymWrapper(env)

Args = namedtuple('Args', ['agent_num',
                           'hid_size',
                           'obs_size',
                           'continuous',
                           'action_dim',
                           'comm_iters',
                           'init_std',
                           'lrate',
                           'batch_size',
                           'max_steps',
                           'gamma',
                           'mean_ratio',
                           'normalize_rewards',
                           'advantages_per_action',
                           'value_coeff',
                           'entr',
                           'action_num'
                          ]
                 )

args = Args(agent_num=env.get_num_of_agents(),
            hid_size=128,
            obs_size=np.max(env.get_shape_of_obs()),
            continuous=False,
            action_dim=np.max(env.get_output_shape_of_act()),
            comm_iters=1,
            init_std=0.01,
            lrate=1e-5,
            batch_size=1024,
            max_steps=2000,
            gamma=0.99,
            mean_ratio=0.0,
            normalize_rewards=False,
            advantages_per_action=False,
            value_coeff=0.0,
            entr=1e-5,
            action_num=np.max(env.get_input_shape_of_act())
           )

policy_net = CommNet(args)
num_epoch = 1000
epoch = 0
for i in range(num_epoch):
    train = Trainer(args, policy_net, env())
    train.train_batch()
    print ('This is the epoch: {}, the time step is {} and the current advantage is: {}'.format(epoch, train.stats['num_steps'], train.stats['action_loss']))
    epoch += 1
    if i%10 == 0:
        print ('The model is saved!')
        torch.save(policy_net, './exp1/coop.pt')