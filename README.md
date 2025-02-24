# Hyperparameter optimization for Deep Reinforcement Learning

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

This README provides source code and results used for the written assignment "*Hyperparameter optimization for Deep Reinforcement Learning to play Atari Pong*" of the IU course: **Reinforcement Learning**.


## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Maintainers](#maintainers)

## Background

The goal of this written assignment was to investigate the difference between using random search and Bayesian optimization (BO) for hyperparameter tuning of Proximity Policy Optimization (PPO). For this comparison, the Atari 2600 Pong environment is used. Given 50 trials for each approach with reduced number of timestep, the best results for each technique have been determined and compared for an extended comparison with an increased number of total timesteps. Additional and detailed information about the methodology applied can be found in the written assignment.

## Folder and file structure

The repository is comprised of the following folders and files:

- `analysis` folder that contains a Jupyter Notebook used for analysing results achieved within the `results` folder

- `config` folder that includes .yaml files that can be used to reproduce simulation of the best trials for PPO and random search as explained in [Usage](#usage)

- `plots` folder which includes a set of visualizations created for the written assignment and stores as .pdf files

- `results` folder which includes all results achieved for BO and random search in corresponding reports as .csv files. It also includes a trained model that can be used along with evaluations during the training process for the best trials in the subfolder `gp-PongNoFrameskip-v4_21` for BO and `randon-PongNoFrameskip-v4_23` for random search.

- `updatedfiles` folder that inlcudes Python files that must be replaced for reproducing results using RL Baselines3 library as explained in [Usage](#usage)

- `requirements.txt` file to run the Jupyter Notebook for analysis. Installation is explained in [Install](#install)


## Install

This project uses [Python](https://www.python.org/) with version 3.10.6 which can be installed using a virtual environment such as [conda](https://anaconda.org/anaconda/conda). For running the Jupyter Notebook `analysis/results_analysis.ipynb` install all requirements included in the `requirements.txt` file using:

```sh
$ pip install -r requirements.txt
```

To reproduce the results achieved you need to clone the separate repository [RL Baselines3 ZOO](https://github.com/DLR-RM/rl-baselines3-zoo) and install all requirements listed in the corresponding documentation. Afterwards you need to replace all files in the cloned repository by those files found in the folder `updated_files`.

## Usage

You can run the Jupyter Notebook cells based on the virtual environment created to analyse all results and create figures that have been used in the written assignment.

For reproducint all results you need conduct the following steps:

1. For running the optimization for random search you need to type the following command within the cloned and adjusted RL Baselines3 Zoo repository:

```sh
$ python train.py --algo ppo --env PongNoFrameskip-v4 --optimize --sampler gp --pruner none  --n-trials 50 --n-jobs 10 --n-timesteps 500000 --optimization-log-path logs/ppo --seed 170194
```

2. For running the optimization for Bayesian optimization you need to type the following command:

```sh
$ python train.py --algo random --env PongNoFrameskip-v4 --optimize --sampler gp --pruner none  --n-trials 50 --n-jobs 10 --n-timesteps 500000 --optimization-log-path logs/ppo --seed 170194
```

3. For running the best results you need to use the .yaml files in the `config` folder and run the following commands (with additional tensorboard logging):

```sh
$ python3.9 train.py --algo ppo --env PongNoFrameskip-v4 --conf-file bo_best_config.yml  --tensorboard-log ./ --seed 170194
```

4. and for Bayesian optimization:

```sh
$ python3.9 train.py --algo ppo --env PongNoFrameskip-v4 --conf-file random_best_config.yml  --tensorboard-log ./ --seed 170194
```

## Maintainers

[@peter1706](https://github.com/peter1706/).