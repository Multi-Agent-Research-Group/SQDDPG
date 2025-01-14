from collections import namedtuple
from models.maddpg import *
from models.m3ddpg import *
from models.sqddpg import *
from models.independent_ac import *
from models.independent_ddpg import *
from models.coma_fc import *



maddpgArgs = namedtuple( 'maddpgArgs', [] )

m3ddpgArgs = namedtuple( 'm3ddpgArgs', [] )

randomArgs = namedtuple( 'randomArgs', [] )

sqddpgArgs = namedtuple( 'sqddpgArgs', ['sample_size'] )

independentArgs = namedtuple( 'independentArgs', [] )

comafcArgs = namedtuple( 'comafcArgs', [] )



Model = dict(maddpg=MADDPG,
             m3ddpg=M3DDPG,
             sqddpg=SQDDPG,
             independent_ac=IndependentAC,
             independent_ddpg=IndependentDDPG,
             coma_fc=COMAFC
            )



AuxArgs = dict(maddpg=maddpgArgs,
               m3ddpg=m3ddpgArgs,
               sqddpg=sqddpgArgs,
               independent_ac=independentArgs,
               independent_ddpg=independentArgs,
               coma_fc=comafcArgs
              )



Strategy=dict(maddpg='pg',
              m3ddpg='pg',
              sqddpg='pg',
              independent_ac='pg',
              independent_ddpg='pg',
              coma_fc='pg'
             )



Args = namedtuple('Args', ['model_name',
                           'agent_num',
                           'hid_size',
                           'obs_size',
                           'continuous',
                           'action_dim',
                           'init_std',
                           'policy_lrate',
                           'value_lrate',
                           'max_steps',
                           'batch_size', # steps<-online/episodes<-offline
                           'gamma',
                           'adv_eps',
                           'adv_eps_s',
                           'use_m3ddpg_bad',
                           'num_adversaries',
                           'use_m3ddpg_good',
                           'normalize_advantages',
                           'entr',
                           'entr_inc',
                           'action_num',
                           'q_func',
                           'train_episodes_num',
                           'replay',
                           'replay_buffer_size',
                           'replay_warmup',
                           'cuda',
                           'grad_clip',
                           'save_model_freq', # episodes
                           'target',
                           'target_lr',
                           'behaviour_update_freq', # steps<-online/episodes<-offline
                           'critic_update_times',
                           'target_update_freq', # steps<-online/episodes<-offline
                           'gumbel_softmax',
                           'epsilon_softmax',
                           'online',
                           'reward_record_type',
                           'shared_parameters' # boolean
                          ]
                 )
