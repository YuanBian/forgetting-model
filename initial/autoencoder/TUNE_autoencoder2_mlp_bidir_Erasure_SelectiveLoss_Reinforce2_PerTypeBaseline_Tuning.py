#!/bin/sh
for i in {1..100}
do
   ~/python-py37-mhahn autoencoder2_mlp_bidir_Erasure_SelectiveLoss_Reinforce2_PerTypeBaseline_Tuning.py >> ~/scr/reinforce-logs/slurm/TUNE_autoencoder2_mlp_bidir_Erasure_SelectiveLoss_Reinforce2_PerTypeBaseline_Tuning.py.txt
done


