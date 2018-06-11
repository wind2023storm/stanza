"""
Training and evaluation for lemmatizer.
"""

import os
import shutil
import time
from datetime import datetime
import argparse
import numpy as np
import random
import torch
from torch import nn, optim
from torch.autograd import Variable

from models.lemma.loader import DataLoader
from models.lemma.vocab import Vocab
from models.lemma.trainer import Trainer
from models.lemma import scorer
from models.common import utils, param
import models.common.seq2seq_constant as constant

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str, default='data/lemma', help='Directory for all lemma data.')
parser.add_argument('--train_file', type=str, default=None, help='Input file for data loader.')
parser.add_argument('--eval_file', type=str, default=None, help='Input file for data loader.')
parser.add_argument('--output_file', type=str, default=None, help='Output CoNLL-U file.')
parser.add_argument('--gold_file', type=str, default=None, help='Output CoNLL-U file.')

parser.add_argument('--mode', default='train', choices=['train', 'predict'])
parser.add_argument('--lang', type=str, help='Language')
parser.add_argument('--best_param', action='store_true', help='Train with best language-specific parameters on record.')

parser.add_argument('--hidden_dim', type=int, default=100)
parser.add_argument('--emb_dim', type=int, default=50)
parser.add_argument('--num_layers', type=int, default=1)
parser.add_argument('--emb_dropout', type=float, default=0.5)
parser.add_argument('--dropout', type=float, default=0.5)
parser.add_argument('--max_dec_len', type=int, default=50)
parser.add_argument('--beam_size', type=int, default=1)

parser.add_argument('--attn_type', default='soft', choices=['soft', 'mlp', 'linear', 'deep'], help='Attention type')
parser.add_argument('-e2d','--enc2dec', default='no', choices=['no', 'linear', 'nonlinear', 'zero'], help='Use an encoder to decoder transformation layer')

parser.add_argument('--sample_train', type=float, default=1.0, help='Subsample training data.')
parser.add_argument('--optim', type=str, default='adam', help='sgd, adagrad, adam or adamax.')
parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
parser.add_argument('--lr_decay', type=float, default=0.9)
parser.add_argument('--decay_epoch', type=int, default=30, help="Decay the lr starting from this epoch.")
parser.add_argument('--num_epoch', type=int, default=30)
parser.add_argument('--batch_size', type=int, default=50)
parser.add_argument('--max_grad_norm', type=float, default=5.0, help='Gradient clipping.')
parser.add_argument('--log_step', type=int, default=20, help='Print log every k steps.')
parser.add_argument('--save_dir', type=str, default='saved_models/lemma', help='Root dir for saving models.')
parser.add_argument('--save_name', type=str, default=None, help="File name to save the model")

parser.add_argument('--seed', type=int, default=1234)
parser.add_argument('--cuda', type=bool, default=torch.cuda.is_available())
parser.add_argument('--cpu', action='store_true', help='Ignore CUDA.')
args = parser.parse_args()

torch.manual_seed(args.seed)
np.random.seed(args.seed)
random.seed(1234)
if args.cpu:
    args.cuda = False
elif args.cuda:
    torch.cuda.manual_seed(args.seed)

args = vars(args)
print("Running lemmatizer in {} mode".format(args['mode']))

if args['mode'] == 'train':
    # load data
    print("Loading data from {} with batch size {}...".format(args['data_dir'], args['batch_size']))
    train_batch = DataLoader('{}/{}'.format(args['data_dir'], args['train_file']), args['batch_size'], args, evaluation=False)
    vocab = train_batch.vocab
    args['vocab_size'] = vocab.size
    dev_batch = DataLoader('{}/{}'.format(args['data_dir'], args['eval_file']), args['batch_size'], args, evaluation=True)
    
    model_file = args['save_dir'] + '/' + args['save_name'] if args['save_name'] is not None \
            else '{}/{}_lemmatizer.pt'.format(args['save_dir'], args['lang'])
    args['save_name'] = model_file
    
    # pred and gold path
    system_pred_file = args['data_dir'] + '/' + args['output_file']
    gold_file = args['gold_file']
    
    # activate param manager and save config
    param_manager = param.ParamManager('params/lemma', args['lang'])
    if args['best_param']: # use best param in file, otherwise use command line params
        args = param_manager.load_to_args(args)
    utils.save_config(args, '{}/{}_config.json'.format(args['save_dir'], args['lang']))
    
    trainer = Trainer(args, vocab)
    
    global_step = 0
    max_steps = len(train_batch) * args['num_epoch']
    dev_score_history = []
    current_lr = args['lr']
    global_start_time = time.time()
    format_str = '{}: step {}/{} (epoch {}/{}), loss = {:.6f} ({:.3f} sec/batch), lr: {:.6f}'
    
    # start training
    for epoch in range(1, args['num_epoch']+1):
        train_loss = 0
        for i, batch in enumerate(train_batch):
            start_time = time.time()
            global_step += 1
            loss = trainer.update(batch, eval=False) # update step
            train_loss += loss
            if global_step % args['log_step'] == 0:
                duration = time.time() - start_time
                print(format_str.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), global_step,\
                        max_steps, epoch, args['num_epoch'], loss, duration, current_lr))
    
        # eval on dev
        print("Evaluating on dev set...")
        dev_preds = []
        for i, batch in enumerate(dev_batch):
            preds = trainer.predict(batch)
            dev_preds += preds
        dev_batch.conll.write_conll_with_lemmas(dev_preds, system_pred_file)
        _, _, dev_score = scorer.score(system_pred_file, gold_file)
        
        train_loss = train_loss / train_batch.num_examples * args['batch_size'] # avg loss per batch
        print("epoch {}: train_loss = {:.6f}, dev_score = {:.4f}".format(epoch, train_loss, dev_score))
    
        # save best model
        if epoch == 1 or dev_score > max(dev_score_history):
            trainer.save(args['save_name'])
            print("new best model saved.")
        
        # lr schedule
        if epoch > args['decay_epoch'] and dev_score <= dev_score_history[-1] and \
                args['optim'] in ['sgd', 'adagrad']:
            current_lr *= args['lr_decay']
            trainer.update_lr(current_lr)
    
        dev_score_history += [dev_score]
        print("")
    
    print("Training ended with {} epochs.".format(epoch))
    
    best_f, best_epoch = max(dev_score_history)*100, np.argmax(dev_score_history)+1
    print("Best dev F1 = {:.2f}, at epoch = {}".format(best_f, best_epoch))

    param_manager.update(args, best_f)

else:
    # load config
    config_file = '{}/{}_config.json'.format(args['save_dir'], args['lang'])
    loaded_args = utils.load_config(config_file)
    # laod data
    print("Loading data from {} with batch size {}...".format(args['data_dir'], args['batch_size']))
    batch = DataLoader('{}/{}'.format(args['data_dir'], args['eval_file']), args['batch_size'], loaded_args, evaluation=True)
    vocab = batch.vocab
    
    # file paths
    system_pred_file = args['data_dir'] + '/' + args['output_file']
    gold_file = args['gold_file']
    model_file = loaded_args['save_name']

    trainer = Trainer(loaded_args, vocab)
    trainer.load(model_file)
    
    print("Start evaluation...")
    preds = []
    for i, b in enumerate(batch):
        preds += trainer.predict(b)
    batch.conll.write_conll_with_lemmas(preds, system_pred_file)
    _, _, score = scorer.score(system_pred_file, gold_file)
    
    print("Lemma score:")
    print("{}\t{:.2f}".format(args['lang'], score*100))


