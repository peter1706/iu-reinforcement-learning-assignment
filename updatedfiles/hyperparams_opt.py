from typing import Any

import numpy as np
import optuna
from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
from torch import nn as nn

from rl_zoo3 import linear_schedule


def sample_ppo_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for PPO hyperparams. Adapted for Pong hyperparameter optimization.

    :param trial:
    :return:
    """
    # batch size should be hyperparam - specifies the minibatch size, so the subset of
    # batch/buffer with random shuffling, those that are sampled from the collected experiences
    # must be smaller or equal to the n_steps
    # TODO recommendet to use batch_size that is a factor of n_steps * n_envs
    # so the rollout buffer size (n_steps * n_envs) should be a multiple of the mini-batch size
    batch_size = trial.suggest_categorical("batch_size", [4, 8, 16, 32, 64, 128, 256, 512])
    
    # specifies number of steps for each env per update -> thereby specifies rollout buffer which is n_steps * n_envs
    # is the number of experiences collected from a SINGLE environment once its next update is performed
    # must be greater or equal to the batch_size
    n_steps = trial.suggest_categorical("n_steps", [4, 8, 16, 32, 64, 128, 256, 512, 1024])
    
    # discount factor gamma
    gamma = trial.suggest_categorical("gamma", [0.8, 0.85, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    
    # starting learning rate 
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    
    # entropy coefficient for controlong weight of the entropy term in the loss function
    ent_coef = trial.suggest_float("ent_coef", 0.00000001, 0.05, log=True)
    
    # clip range for limiting changes to the policy during optimization
    clip_range = trial.suggest_categorical("clip_range", [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4])
    
    # how often each of data fro rollout buffer is used to perform gradient updates
    n_epochs = trial.suggest_categorical("n_epochs", [1, 3, 5, 7, 10, 15, 20])
    
    # for trade-off between bias and variance in advantage estimates
    gae_lambda = trial.suggest_categorical("gae_lambda", [0.8, 0.85, 0.9, 0.92, 0.95, 0.98, 0.99, 1.0])
    
    # used to clip gradients during optmization step
    max_grad_norm = trial.suggest_categorical("max_grad_norm", [0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    
    # value function coefficient
    vf_coef = trial.suggest_float("vf_coef", 0.1, 1)
    
    # net architecture
    net_arch_type = trial.suggest_categorical("net_arch", ["identity", "small", "medium", "medium_pi", "medium_vf", "large"])
    
    # orthogonal initialization
    ortho_init = trial.suggest_categorical('ortho_init', [False, True])
    
    # different activation functions for the policy network 
    activation_fn_name = trial.suggest_categorical("activation_fn", ["sigmoid", "tanh", "relu", "elu", "leaky_relu"])
    
    
    # lr_schedule = "constant"
    # Uncomment to enable learning rate schedule
    # TODO perhaps it is an idea to use learning rate scheduling to have adaptive learning rates
    # linear decaay reduces leraning rate gradually over time
    # or using Adam Optimizer (defuault ???)
    
    # lr_schedule = trial.suggest_categorical('lr_schedule', ['linear', 'constant'])
    # if lr_schedule == "linear":
    #     learning_rate = linear_schedule(learning_rate)
    

    # TODO: account when using multiple envs (buffer size is correct)
    # check buffer size
    if batch_size > n_steps:
        batch_size = n_steps
        
    # use CNN policy
    policy = "CnnPolicy"

    # Independent networks usually work best
    # when not working with images
    # for CnnPolicy this defines the FFNN after the CNN
    net_arch = {
        "identity": None,
        "small": dict(pi=[64], vf=[64]),
        "medium": dict(pi=[64, 64], vf=[64, 64]),
        "medium_pi": dict(pi=[64], vf=[64, 64]),
        "medium_vf": dict(pi=[64, 64], vf=[64]),
        "large": dict(pi=[256, 256], vf=[256, 256]),
    }[net_arch_type]

    # activation function used
    activation_fn = {"sigmoid": nn.Sigmoid, "tanh": nn.Tanh, "relu": nn.ReLU, "elu": nn.ELU, "leaky_relu": nn.LeakyReLU}[activation_fn_name]

    return {
        "n_steps": n_steps,
        "batch_size": batch_size,
        "gamma": gamma,
        "learning_rate": learning_rate,
        "ent_coef": ent_coef,
        "clip_range": clip_range,
        "n_epochs": n_epochs,
        "gae_lambda": gae_lambda,
        "max_grad_norm": max_grad_norm,
        "vf_coef": vf_coef,
        "policy": policy,
        "policy_kwargs": dict(
            net_arch=net_arch,
            activation_fn=activation_fn,
            ortho_init=ortho_init,
        ),
    }


def sample_ppo_lstm_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for RecurrentPPO hyperparams.
    uses sample_ppo_params(), this function samples for the policy_kwargs
    :param trial:
    :return:
    """
    hyperparams = sample_ppo_params(trial, n_actions, n_envs, additional_args)

    enable_critic_lstm = trial.suggest_categorical("enable_critic_lstm", [False, True])
    lstm_hidden_size = trial.suggest_categorical("lstm_hidden_size", [16, 32, 64, 128, 256, 512])

    hyperparams["policy_kwargs"].update(
        {
            "enable_critic_lstm": enable_critic_lstm,
            "lstm_hidden_size": lstm_hidden_size,
        }
    )

    return hyperparams


def sample_trpo_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for TRPO hyperparams.

    :param trial:
    :return:
    """
    batch_size = trial.suggest_categorical("batch_size", [8, 16, 32, 64, 128, 256, 512])
    n_steps = trial.suggest_categorical("n_steps", [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
    gamma = trial.suggest_categorical("gamma", [0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    # line_search_shrinking_factor = trial.suggest_categorical("line_search_shrinking_factor", [0.6, 0.7, 0.8, 0.9])
    n_critic_updates = trial.suggest_categorical("n_critic_updates", [5, 10, 20, 25, 30])
    cg_max_steps = trial.suggest_categorical("cg_max_steps", [5, 10, 20, 25, 30])
    # cg_damping = trial.suggest_categorical("cg_damping", [0.5, 0.2, 0.1, 0.05, 0.01])
    target_kl = trial.suggest_categorical("target_kl", [0.1, 0.05, 0.03, 0.02, 0.01, 0.005, 0.001])
    gae_lambda = trial.suggest_categorical("gae_lambda", [0.8, 0.9, 0.92, 0.95, 0.98, 0.99, 1.0])
    net_arch_type = trial.suggest_categorical("net_arch", ["small", "medium"])
    # Uncomment for gSDE (continuous actions)
    # log_std_init = trial.suggest_float("log_std_init", -4, 1)
    # Uncomment for gSDE (continuous action)
    # sde_sample_freq = trial.suggest_categorical("sde_sample_freq", [-1, 8, 16, 32, 64, 128, 256])
    # Orthogonal initialization
    ortho_init = False
    # ortho_init = trial.suggest_categorical('ortho_init', [False, True])
    # activation_fn = trial.suggest_categorical('activation_fn', ['tanh', 'relu', 'elu', 'leaky_relu'])
    activation_fn_name = trial.suggest_categorical("activation_fn", ["tanh", "relu"])
    # lr_schedule = "constant"
    # Uncomment to enable learning rate schedule
    # lr_schedule = trial.suggest_categorical('lr_schedule', ['linear', 'constant'])
    # if lr_schedule == "linear":
    #     learning_rate = linear_schedule(learning_rate)

    # TODO: account when using multiple envs
    if batch_size > n_steps:
        batch_size = n_steps

    # Independent networks usually work best
    # when not working with images
    net_arch = {
        "small": dict(pi=[64, 64], vf=[64, 64]),
        "medium": dict(pi=[256, 256], vf=[256, 256]),
    }[net_arch_type]

    activation_fn = {"tanh": nn.Tanh, "relu": nn.ReLU, "elu": nn.ELU, "leaky_relu": nn.LeakyReLU}[activation_fn_name]

    return {
        "n_steps": n_steps,
        "batch_size": batch_size,
        "gamma": gamma,
        # "cg_damping": cg_damping,
        "cg_max_steps": cg_max_steps,
        # "line_search_shrinking_factor": line_search_shrinking_factor,
        "n_critic_updates": n_critic_updates,
        "target_kl": target_kl,
        "learning_rate": learning_rate,
        "gae_lambda": gae_lambda,
        # "sde_sample_freq": sde_sample_freq,
        "policy_kwargs": dict(
            # log_std_init=log_std_init,
            net_arch=net_arch,
            activation_fn=activation_fn,
            ortho_init=ortho_init,
        ),
    }


def sample_a2c_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for A2C hyperparams. Adapted for Pong hyperparameter optimization

    :param trial:
    :return:
    """
    
    # discount factor gamma
    gamma = trial.suggest_categorical("gamma", [0.8, 0.85, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    
    # used to clip gradients during optmization step
    max_grad_norm = trial.suggest_categorical("max_grad_norm", [0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    
    # Toggle PyTorch RMS Prop (different from TF one, cf doc) - rmsprop-True or Adam optimizer-False
    # could also add the hyperparameter rms_prop_eps, but only if RMSProp is being selected
    use_rms_prop = trial.suggest_categorical("use_rms_prop", [False, True])
    
    # for trade-off between bias and variance in advantage estimates
    gae_lambda = trial.suggest_categorical("gae_lambda", [0.8, 0.85, 0.9, 0.92, 0.95, 0.98, 0.99, 1.0])
    
    # specifies number of steps for each env per update -> thereby specifies rollout buffer which is n_steps * n_envs
    # is the number of experiences collected from a SINGLE environment once its next update is performed
    # must be greater or equal to the batch_size
    n_steps = trial.suggest_categorical("n_steps", [4, 8, 16, 32, 64, 128, 256, 512, 1024])
    
    # starting learning rate 
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    
    # entropy coefficient for controlong weight of the entropy term in the loss function
    ent_coef = trial.suggest_float("ent_coef", 0.00000001, 0.05, log=True)
    
    # value function coefficient
    vf_coef = trial.suggest_float("vf_coef", 0.1, 1)
    
    # orthogonal initialization
    ortho_init = trial.suggest_categorical('ortho_init', [False, True])
    
    # net architecture
    net_arch_type = trial.suggest_categorical("net_arch", ["identity", "small", "medium", "medium_pi", "medium_vf", "large"])
    # sde_net_arch = trial.suggest_categorical("sde_net_arch", [None, "tiny", "small"])
    # full_std = trial.suggest_categorical("full_std", [False, True])
    
    # different activation functions for the policy network 
    activation_fn_name = trial.suggest_categorical("activation_fn", ["sigmoid", "tanh", "relu", "elu", "leaky_relu"])

    # use CNN policy
    policy = "CnnPolicy"

    # Independent networks usually work best
    # when not working with images
    # for CnnPolicy this defines the FFNN after the CNN
    net_arch = {
        "identity": None,
        "small": dict(pi=[64], vf=[64]),
        "medium": dict(pi=[64, 64], vf=[64, 64]),
        "medium_pi": dict(pi=[64], vf=[64, 64]),
        "medium_vf": dict(pi=[64, 64], vf=[64]),
        "large": dict(pi=[256, 256], vf=[256, 256]),
    }[net_arch_type]

    # activation function used
    activation_fn = {"sigmoid": nn.Sigmoid, "tanh": nn.Tanh, "relu": nn.ReLU, "elu": nn.ELU, "leaky_relu": nn.LeakyReLU}[activation_fn_name]

    # use CNN policy
    policy = "CnnPolicy"

    return {
        "n_steps": n_steps,
        "gamma": gamma,
        "gae_lambda": gae_lambda,
        "learning_rate": learning_rate,
        "ent_coef": ent_coef,
        "max_grad_norm": max_grad_norm,
        "use_rms_prop": use_rms_prop,
        "vf_coef": vf_coef,
        "policy": policy,
        "policy_kwargs": dict(
            net_arch=net_arch,
            activation_fn=activation_fn,
            ortho_init=ortho_init,
        ),
    }


def sample_sac_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for SAC hyperparams.

    :param trial:
    :return:
    """
    gamma = trial.suggest_categorical("gamma", [0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128, 256, 512, 1024, 2048])
    buffer_size = trial.suggest_categorical("buffer_size", [int(1e4), int(1e5), int(1e6)])
    learning_starts = trial.suggest_categorical("learning_starts", [0, 1000, 10000, 20000])
    # train_freq = trial.suggest_categorical('train_freq', [1, 10, 100, 300])
    train_freq = trial.suggest_categorical("train_freq", [1, 4, 8, 16, 32, 64, 128, 256, 512])
    # Polyak coeff
    tau = trial.suggest_categorical("tau", [0.001, 0.005, 0.01, 0.02, 0.05, 0.08])
    # gradient_steps takes too much time
    # gradient_steps = trial.suggest_categorical('gradient_steps', [1, 100, 300])
    gradient_steps = train_freq
    # ent_coef = trial.suggest_categorical('ent_coef', ['auto', 0.5, 0.1, 0.05, 0.01, 0.0001])
    ent_coef = "auto"
    # You can comment that out when not using gSDE
    log_std_init = trial.suggest_float("log_std_init", -4, 1)
    # NOTE: Add "verybig" to net_arch when tuning HER
    net_arch_type = trial.suggest_categorical("net_arch", ["small", "medium", "big"])
    # activation_fn = trial.suggest_categorical('activation_fn', [nn.Tanh, nn.ReLU, nn.ELU, nn.LeakyReLU])

    net_arch = {
        "small": [64, 64],
        "medium": [256, 256],
        "big": [400, 300],
        # Uncomment for tuning HER
        # "large": [256, 256, 256],
        # "verybig": [512, 512, 512],
    }[net_arch_type]

    target_entropy = "auto"
    # if ent_coef == 'auto':
    #     # target_entropy = trial.suggest_categorical('target_entropy', ['auto', 5, 1, 0, -1, -5, -10, -20, -50])
    #     target_entropy = trial.suggest_float('target_entropy', -10, 10)

    hyperparams = {
        "gamma": gamma,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "buffer_size": buffer_size,
        "learning_starts": learning_starts,
        "train_freq": train_freq,
        "gradient_steps": gradient_steps,
        "ent_coef": ent_coef,
        "tau": tau,
        "target_entropy": target_entropy,
        "policy_kwargs": dict(log_std_init=log_std_init, net_arch=net_arch),
    }

    if additional_args["using_her_replay_buffer"]:
        hyperparams = sample_her_params(trial, hyperparams, additional_args["her_kwargs"])

    return hyperparams


def sample_td3_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for TD3 hyperparams.

    :param trial:
    :return:
    """
    gamma = trial.suggest_categorical("gamma", [0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 100, 128, 256, 512, 1024, 2048])
    buffer_size = trial.suggest_categorical("buffer_size", [int(1e4), int(1e5), int(1e6)])
    # Polyak coeff
    tau = trial.suggest_categorical("tau", [0.001, 0.005, 0.01, 0.02, 0.05, 0.08])

    train_freq = trial.suggest_categorical("train_freq", [1, 4, 8, 16, 32, 64, 128, 256, 512])
    gradient_steps = train_freq

    noise_type = trial.suggest_categorical("noise_type", ["ornstein-uhlenbeck", "normal", None])
    noise_std = trial.suggest_float("noise_std", 0, 1)

    # NOTE: Add "verybig" to net_arch when tuning HER
    net_arch_type = trial.suggest_categorical("net_arch", ["small", "medium", "big"])
    # activation_fn = trial.suggest_categorical('activation_fn', [nn.Tanh, nn.ReLU, nn.ELU, nn.LeakyReLU])

    net_arch = {
        "small": [64, 64],
        "medium": [256, 256],
        "big": [400, 300],
        # Uncomment for tuning HER
        # "verybig": [256, 256, 256],
    }[net_arch_type]

    hyperparams = {
        "gamma": gamma,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "buffer_size": buffer_size,
        "train_freq": train_freq,
        "gradient_steps": gradient_steps,
        "policy_kwargs": dict(net_arch=net_arch),
        "tau": tau,
    }

    if noise_type == "normal":
        hyperparams["action_noise"] = NormalActionNoise(mean=np.zeros(n_actions), sigma=noise_std * np.ones(n_actions))
    elif noise_type == "ornstein-uhlenbeck":
        hyperparams["action_noise"] = OrnsteinUhlenbeckActionNoise(
            mean=np.zeros(n_actions), sigma=noise_std * np.ones(n_actions)
        )

    if additional_args["using_her_replay_buffer"]:
        hyperparams = sample_her_params(trial, hyperparams, additional_args["her_kwargs"])

    return hyperparams


def sample_ddpg_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for DDPG hyperparams.

    :param trial:
    :return:
    """
    gamma = trial.suggest_categorical("gamma", [0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 100, 128, 256, 512, 1024, 2048])
    buffer_size = trial.suggest_categorical("buffer_size", [int(1e4), int(1e5), int(1e6)])
    # Polyak coeff
    tau = trial.suggest_categorical("tau", [0.001, 0.005, 0.01, 0.02, 0.05, 0.08])

    train_freq = trial.suggest_categorical("train_freq", [1, 4, 8, 16, 32, 64, 128, 256, 512])
    gradient_steps = train_freq

    noise_type = trial.suggest_categorical("noise_type", ["ornstein-uhlenbeck", "normal", None])
    noise_std = trial.suggest_float("noise_std", 0, 1)

    # NOTE: Add "verybig" to net_arch when tuning HER (see TD3)
    net_arch_type = trial.suggest_categorical("net_arch", ["small", "medium", "big"])
    # activation_fn = trial.suggest_categorical('activation_fn', [nn.Tanh, nn.ReLU, nn.ELU, nn.LeakyReLU])

    net_arch = {
        "small": [64, 64],
        "medium": [256, 256],
        "big": [400, 300],
    }[net_arch_type]

    hyperparams = {
        "gamma": gamma,
        "tau": tau,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "buffer_size": buffer_size,
        "train_freq": train_freq,
        "gradient_steps": gradient_steps,
        "policy_kwargs": dict(net_arch=net_arch),
    }

    if noise_type == "normal":
        hyperparams["action_noise"] = NormalActionNoise(mean=np.zeros(n_actions), sigma=noise_std * np.ones(n_actions))
    elif noise_type == "ornstein-uhlenbeck":
        hyperparams["action_noise"] = OrnsteinUhlenbeckActionNoise(
            mean=np.zeros(n_actions), sigma=noise_std * np.ones(n_actions)
        )

    if additional_args["using_her_replay_buffer"]:
        hyperparams = sample_her_params(trial, hyperparams, additional_args["her_kwargs"])

    return hyperparams


def sample_dqn_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for DQN hyperparams. Adapted for Pong hyperparameter optimization.

    :param trial:
    :return:
    """
    # discount factor gamma
    gamma = trial.suggest_categorical("gamma", [0.8, 0.85, 0.9, 0.95, 0.98, 0.99, 0.995, 0.999, 0.9999])
    
    # starting learning rate 
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    
    # batch size should be hyperparam - specifies the minibatch size, so the subset of
    # batch/buffer with random shuffling, those that are sampled from the collected experiences
    # must be smaller or equal to the n_steps
    # TODO recommendet to use batch_size that is a factor of n_steps * n_envs
    # so the rollout buffer size (n_steps * n_envs) should be a multiple of the mini-batch size
    batch_size = trial.suggest_categorical("batch_size", [4, 8, 16, 32, 64, 128, 256, 512])

    # specifies buffer size which refers to the maximum number of transitions stored in the replay buffer
    buffer_size = trial.suggest_categorical("buffer_size", [int(1e4), int(5e4), int(1e5), int(5e5), int(1e6)])
    
    # controls final value of epsiolon in the epsilon-greedy exploration strategy
    # determines the minimum probability of selecting a random action rather than the action
    # predicted by the policy
    # TODO should check what is the default starting value for eps (inital)
    exploration_final_eps = trial.suggest_float("exploration_final_eps", 0.01, 0.2)
    
    # fraction over entire training period over which the exploration rate is reducted
    # basically controls how quickly epiolon decaas from its initial state (exploration initi)
    # to its final value
    # specifies fraction of total time steps during which this decay occurs
    exploration_fraction = trial.suggest_float("exploration_fraction", 0.1, 0.5)
    
    # specified how often the target network is updated every -- steps
    target_update_interval = trial.suggest_categorical("target_update_interval", [1000, 5000, 10000, 15000, 20000, 50000])
    
    # how many steps of the model to collect transitions for before learning starts
    # this means before updating Q-values (so basically before it only collects experiences
    # and stores them in the replay buffer but does not perform gradient updates)
    learning_starts = trial.suggest_categorical("learning_starts", [1000, 2000, 5000, 10000, 20000, 50000])

    # update the model every train_freq steps
    # basically how often the agent should update its Q-network- so frequency of gradient updates
    train_freq = trial.suggest_categorical("train_freq", [1, 4, 8, 16, 128, 256, 1000])
    
    subsample_steps = trial.suggest_categorical("subsample_steps", [1, 2, 4, 8])
    # specifies how many gradient steps to do after each rollout  (if -1 then do as many gradient
    # steps as steps done in the environment during the rollout)
    gradient_steps = max(train_freq // subsample_steps, 1)

    # net architecture
    net_arch_type = trial.suggest_categorical("net_arch", ["identity", "small", "medium", "large"])

    net_arch = {
        "identity": None,
        "small": [64],
        "medium": [64, 64],
        "large": [256, 256],
    }[net_arch_type]
    
    # different activation functions for the policy network 
    activation_fn_name = trial.suggest_categorical("activation_fn", ["sigmoid", "tanh", "relu", "elu", "leaky_relu"])
    
    # activation function used
    activation_fn = {"sigmoid": nn.Sigmoid, "tanh": nn.Tanh, "relu": nn.ReLU, "elu": nn.ELU, "leaky_relu": nn.LeakyReLU}[activation_fn_name]
    
    # TODO orthogonal initialization not possible using DQN policy
    # ortho_init = trial.suggest_categorical('ortho_init', [False, True])
    
    # always use CnnPolicy
    policy = "CnnPolicy"
    

    hyperparams = {
        "gamma": gamma,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "buffer_size": buffer_size,
        "train_freq": train_freq,
        "gradient_steps": gradient_steps,
        "exploration_fraction": exploration_fraction,
        "exploration_final_eps": exploration_final_eps,
        "target_update_interval": target_update_interval,
        "learning_starts": learning_starts,
        "policy": policy,
        "policy_kwargs": dict(
            net_arch=net_arch,
            activation_fn=activation_fn
        ),
    }

    if additional_args["using_her_replay_buffer"]:
        hyperparams = sample_her_params(trial, hyperparams, additional_args["her_kwargs"])

    return hyperparams


def sample_her_params(trial: optuna.Trial, hyperparams: dict[str, Any], her_kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Sampler for HerReplayBuffer hyperparams.

    :param trial:
    :parma hyperparams:
    :return:
    """
    her_kwargs = her_kwargs.copy()
    her_kwargs["n_sampled_goal"] = trial.suggest_int("n_sampled_goal", 1, 5)
    her_kwargs["goal_selection_strategy"] = trial.suggest_categorical(
        "goal_selection_strategy", ["final", "episode", "future"]
    )
    hyperparams["replay_buffer_kwargs"] = her_kwargs
    return hyperparams


def sample_tqc_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for TQC hyperparams.

    :param trial:
    :return:
    """
    # TQC is SAC + Distributional RL
    hyperparams = sample_sac_params(trial, n_actions, n_envs, additional_args)

    n_quantiles = trial.suggest_int("n_quantiles", 5, 50)
    top_quantiles_to_drop_per_net = trial.suggest_int("top_quantiles_to_drop_per_net", 0, n_quantiles - 1)

    hyperparams["policy_kwargs"].update({"n_quantiles": n_quantiles})
    hyperparams["top_quantiles_to_drop_per_net"] = top_quantiles_to_drop_per_net

    return hyperparams


def sample_qrdqn_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for QR-DQN hyperparams.

    :param trial:
    :return:
    """
    # TQC is DQN + Distributional RL
    hyperparams = sample_dqn_params(trial, n_actions, n_envs, additional_args)

    n_quantiles = trial.suggest_int("n_quantiles", 5, 200)
    hyperparams["policy_kwargs"].update({"n_quantiles": n_quantiles})

    return hyperparams


def sample_ars_params(trial: optuna.Trial, n_actions: int, n_envs: int, additional_args: dict) -> dict[str, Any]:
    """
    Sampler for ARS hyperparams.
    :param trial:
    :return:
    """
    # n_eval_episodes = trial.suggest_categorical("n_eval_episodes", [1, 2])
    n_delta = trial.suggest_categorical("n_delta", [4, 8, 6, 32, 64])
    # learning_rate = trial.suggest_categorical("learning_rate", [0.01, 0.02, 0.025, 0.03])
    learning_rate = trial.suggest_float("learning_rate", 1e-5, 1, log=True)
    delta_std = trial.suggest_categorical("delta_std", [0.01, 0.02, 0.025, 0.03, 0.05, 0.1, 0.2, 0.3])
    top_frac_size = trial.suggest_categorical("top_frac_size", [0.1, 0.2, 0.3, 0.5, 0.8, 0.9, 1.0])
    zero_policy = trial.suggest_categorical("zero_policy", [True, False])
    n_top = max(int(top_frac_size * n_delta), 1)

    # net_arch = trial.suggest_categorical("net_arch", ["linear", "tiny", "small"])

    # Note: remove bias to be as the original linear policy
    # and do not squash output
    # Comment out when doing hyperparams search with linear policy only
    # net_arch = {
    #     "linear": [],
    #     "tiny": [16],
    #     "small": [32],
    # }[net_arch]

    # TODO: optimize the alive_bonus_offset too

    return {
        # "n_eval_episodes": n_eval_episodes,
        "n_delta": n_delta,
        "learning_rate": learning_rate,
        "delta_std": delta_std,
        "n_top": n_top,
        "zero_policy": zero_policy,
        # "policy_kwargs": dict(net_arch=net_arch),
    }


HYPERPARAMS_SAMPLER = {
    "a2c": sample_a2c_params,
    "ars": sample_ars_params,
    "ddpg": sample_ddpg_params,
    "dqn": sample_dqn_params,
    "qrdqn": sample_qrdqn_params,
    "sac": sample_sac_params,
    "tqc": sample_tqc_params,
    "ppo": sample_ppo_params,
    "ppo_lstm": sample_ppo_lstm_params,
    "td3": sample_td3_params,
    "trpo": sample_trpo_params,
}
