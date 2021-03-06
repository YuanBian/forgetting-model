# 11
# Based on 2 and 4 and 7_Both
# Reparameterized

print("Character aware!")

# Character-aware version of the `Tabula Rasa' language model
# char-lm-ud-stationary-vocab-wiki-nospaces-bptt-2-words_NoNewWeightDrop.py
# Adopted for English and German
import sys

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--language", dest="language", type=str, default="english")
parser.add_argument("--load-from-lm", dest="load_from_lm", type=str, default=964163553)

import random

parser.add_argument("--batchSize", type=int, default=random.choice([128]))
parser.add_argument("--word_embedding_size", type=int, default=random.choice([512]))
parser.add_argument("--hidden_dim", type=int, default=random.choice([1024]))
parser.add_argument("--layer_num", type=int, default=random.choice([2]))
parser.add_argument("--weight_dropout_in", type=float, default=random.choice([0.05]))
parser.add_argument("--weight_dropout_out", type=float, default=random.choice([0.05]))
parser.add_argument("--char_dropout_prob", type=float, default=random.choice([0.01]))
#parser.add_argument("--char_noise_prob", type = float, default=random.choice([0.0]))
parser.add_argument("--learning_rate", type = float, default= random.choice([0.0001]))
parser.add_argument("--myID", type=int, default=random.randint(0,1000000000))
parser.add_argument("--sequence_length", type=int, default=random.choice([20]))
parser.add_argument("--verbose", type=bool, default=False)
parser.add_argument("--lr_decay", type=float, default=random.choice([1.0]))

parser.add_argument("--reward_multiplier_baseline", type=float, default=0.1)

TRAIN_LM = True
assert TRAIN_LM

parser.add_argument("--RATE_WEIGHT", type=float, default=random.choice([1.1])) #[3.0, 3.5, 4.0, 4.5, 5.0]))
# 1.5, 2.0, 2.5, 

#[1.25, 1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 4.0, 5.0, 6.0])) # 0.5, 0.75, 1.0,  ==> this is essentially the point at which showing is better than guessing
parser.add_argument("--momentum", type=float, default=random.choice([0.0, 0.0, 0.0, 0.3, 0.5, 0.7, 0.9]))
parser.add_argument("--entropy_weight", type=float, default=random.choice([0.0, 0.00001, 0.00005, 0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.0008, 0.001, 0.005])) # 0.0,  0.005, 0.01, 0.1, 0.4]))

parser.add_argument("--tuning", type=int, default=0) #random.choice([0.00001, 0.00005, 0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.0008, 0.001])) # 0.0,  0.005, 0.01, 0.1, 0.4]))

model = "REAL_REAL"

import math

args=parser.parse_args()


print(args.myID)
import sys
if args.tuning == 1:
   sys.stdout = open("/u/scr/mhahn/reinforce-logs-predict/full-logs/"+__file__+"_"+str(args.myID), "w")

print(args)



import corpusIteratorWikiWords



def plus(it1, it2):
   for x in it1:
      yield x
   for x in it2:
      yield x

char_vocab_path = "vocabularies/"+args.language.lower()+"-wiki-word-vocab-50000.txt"

with open(char_vocab_path, "r") as inFile:
     itos = [x.split("\t")[0] for x in inFile.read().strip().split("\n")[:50000]]
stoi = dict([(itos[i],i) for i in range(len(itos))])


itos_total = ["<SOS>", "<EOS>", "OOV"] + itos
stoi_total = dict([(itos_total[i],i) for i in range(len(itos_total))])


with open("vocabularies/char-vocab-wiki-"+args.language, "r") as inFile:
     itos_chars = [x for x in inFile.read().strip().split("\n")]
stoi_chars = dict([(itos_chars[i],i) for i in range(len(itos_chars))])


itos_chars_total = ["<SOS>", "<EOS>", "OOV"] + itos_chars


import random


import torch

print(torch.__version__)

#from weight_drop import WeightDrop


rnn = torch.nn.LSTM(2*args.word_embedding_size, args.hidden_dim, args.layer_num).cuda()



rnn_drop = rnn #WeightDrop(rnn, layer_names=[(name, args.weight_dropout_in) for name, _ in rnn.named_parameters() if name.startswith("weight_ih_")] + [ (name, args.weight_dropout_hidden) for name, _ in rnn.named_parameters() if name.startswith("weight_hh_")])

output = torch.nn.Linear(args.hidden_dim, len(itos)+3).cuda()

word_embeddings = torch.nn.Embedding(num_embeddings=len(itos)+3, embedding_dim=2*args.word_embedding_size).cuda()



logsoftmax = torch.nn.LogSoftmax(dim=2)

train_loss = torch.nn.NLLLoss(ignore_index=0)
print_loss = torch.nn.NLLLoss(size_average=False, reduce=False, ignore_index=0)
char_dropout = torch.nn.Dropout2d(p=args.char_dropout_prob)


train_loss_chars = torch.nn.NLLLoss(ignore_index=0, reduction='sum')

modules_lm = [rnn, output, word_embeddings]


#character_embeddings = torch.nn.Embedding(num_embeddings = len(itos_chars_total)+3, embedding_dim=args.char_emb_dim).cuda()

memory_mlp_inner = torch.nn.Linear(2*args.word_embedding_size, 500).cuda()
memory_mlp_inner_from_pos = torch.nn.Linear(256, 500).cuda()
memory_mlp_outer = torch.nn.Linear(500, 2).cuda()

sigmoid = torch.nn.Sigmoid()
relu = torch.nn.ReLU()

#character_embeddings = torch.nn.Embedding(num_embeddings = len(itos_chars_total)+3, embedding_dim=args.char_emb_dim).cuda()
#
#char_composition = torch.nn.LSTM(args.char_emb_dim, args.char_enc_hidden_dim, 1, bidirectional=True).cuda()
#char_composition_output = torch.nn.Linear(2*args.char_enc_hidden_dim, args.word_embedding_size).cuda()
#
#char_decoder_rnn = torch.nn.LSTM(args.char_emb_dim + args.hidden_dim, args.char_dec_hidden_dim, 1).cuda()
#char_decoder_output = torch.nn.Linear(args.char_dec_hidden_dim, len(itos_chars_total))
#
#
#modules_autoencoder += [character_embeddings, char_composition, char_composition_output, char_decoder_rnn, char_decoder_output]

positional_embeddings = torch.nn.Embedding(num_embeddings=args.sequence_length+2, embedding_dim=256).cuda()

#perword_baseline_inner = torch.nn.Linear(2*args.word_embedding_size, 500).cuda()
#perword_baseline_outer = torch.nn.Linear(500, 1).cuda()


modules_memory = [memory_mlp_inner, memory_mlp_outer, memory_mlp_inner_from_pos, positional_embeddings]

def parameters_memory():
   for module in modules_memory:
       for param in module.parameters():
            yield param

parameters_memory_cached = [x for x in parameters_memory()]



def parameters_lm():
   for module in modules_lm:
       for param in module.parameters():
            yield param

parameters_lm_cached = [x for x in parameters_lm()]


learning_rate = args.learning_rate

assert TRAIN_LM
optim_memory = torch.optim.SGD(parameters_memory(), lr=learning_rate, momentum=args.momentum) # 0.02, 0.9
optim_lm = torch.optim.SGD(parameters_lm(), lr=learning_rate, momentum=0.0) # 0.02, 0.9

#named_modules = {"rnn" : rnn, "output" : output, "word_embeddings" : word_embeddings, "optim" : optim}

if args.load_from_lm is not None:
  lm_file = "char-lm-ud-stationary-vocab-wiki-nospaces-bptt-2-words_NoNewWeightDrop_NoChars_Erasure.py"
  checkpoint = torch.load("/u/scr/mhahn/CODEBOOKS/"+args.language+"_"+lm_file+"_code_"+str(args.load_from_lm)+".txt")
  for i in range(len(checkpoint["components"])):
      modules_lm[i].load_state_dict(checkpoint["components"][i])

from torch.autograd import Variable


# ([0] + [stoi[training_data[x]]+1 for x in range(b, b+sequence_length) if x < len(training_data)]) 

#from embed_regularize import embedded_dropout



def prepareDatasetChunks(data, train=True):
      numeric = [0]
      count = 0
      print("Prepare chunks")
      numerified = []
      numerified_chars = []
      for chunk in data:
       #print(len(chunk))
       for char in chunk:
#         if char == " ":
 #          continue
         count += 1
#         if count % 100000 == 0:
#             print(count/len(data))
         numerified.append((stoi[char]+3 if char in stoi else 2))
         numerified_chars.append([0] + [stoi_chars[x]+3 if x in stoi_chars else 2 for x in char])

       if len(numerified) > (args.batchSize*args.sequence_length):
         sequenceLengthHere = args.sequence_length

         cutoff = int(len(numerified)/(args.batchSize*sequenceLengthHere)) * (args.batchSize*sequenceLengthHere)
         numerifiedCurrent = numerified[:cutoff]
         numerifiedCurrent_chars = numerified_chars[:cutoff]

         for i in range(len(numerifiedCurrent_chars)):
            numerifiedCurrent_chars[i] = numerifiedCurrent_chars[i][:15] + [1]
            numerifiedCurrent_chars[i] = numerifiedCurrent_chars[i] + ([0]*(16-len(numerifiedCurrent_chars[i])))


         numerified = numerified[cutoff:]
         numerified_chars = numerified_chars[cutoff:]
       
         numerifiedCurrent = torch.LongTensor(numerifiedCurrent).view(args.batchSize, -1, sequenceLengthHere).transpose(0,1).transpose(1,2).cuda()
         numerifiedCurrent_chars = torch.LongTensor(numerifiedCurrent_chars).view(args.batchSize, -1, sequenceLengthHere, 16).transpose(0,1).transpose(1,2).cuda()

         numberOfSequences = numerifiedCurrent.size()[0]
         for i in range(numberOfSequences):
             yield numerifiedCurrent[i], numerifiedCurrent_chars[i]
         hidden = None
       else:
         print("Skipping")




hidden = None

zeroBeginning = torch.LongTensor([0 for _ in range(args.batchSize)]).cuda().view(1,args.batchSize)
beginning = None

zeroBeginning_chars = torch.zeros(1, args.batchSize, 16).long().cuda()


zeroHidden = torch.zeros((args.layer_num, args.batchSize, args.hidden_dim)).cuda()

bernoulli = torch.distributions.bernoulli.Bernoulli(torch.tensor([0.1 for _ in range(args.batchSize)]).cuda())

bernoulli_input = torch.distributions.bernoulli.Bernoulli(torch.tensor([1-args.weight_dropout_in for _ in range(args.batchSize * 2 * args.word_embedding_size)]).cuda())
bernoulli_output = torch.distributions.bernoulli.Bernoulli(torch.tensor([1-args.weight_dropout_out for _ in range(args.batchSize * args.hidden_dim)]).cuda())

#runningAveragePredictionLoss = 1.0
runningAverageReward = 5.0
runningAverageBaselineDeviation = 2.0
runningAveragePredictionLoss = 5.0
expectedRetentionRate = 0.5

def forward(numeric, train=True, printHere=False):
      global hidden
      global beginning
      global beginning_chars
      if hidden is None:
          hidden = None
          beginning = zeroBeginning
   #       beginning_chars = zeroBeginning_chars
      elif hidden is not None:
          hidden1 = Variable(hidden[0]).detach()
          hidden2 = Variable(hidden[1]).detach()
          forRestart = bernoulli.sample()
          hidden1 = torch.where(forRestart.unsqueeze(0).unsqueeze(2) == 1, zeroHidden, hidden1)
          hidden2 = torch.where(forRestart.unsqueeze(0).unsqueeze(2) == 1, zeroHidden, hidden2)
          hidden = (hidden1, hidden2)
          beginning = torch.where(forRestart.unsqueeze(0) == 1, zeroBeginning, beginning)
  #        beginning_chars = torch.where(forRestart.unsqueeze(0).unsqueeze(2) == 1, zeroBeginning_chars, beginning_chars)

      numeric, numeric_chars = numeric
      numeric = torch.cat([beginning, numeric], dim=0)
      embedded_everything = word_embeddings(numeric)

      # Positional embeddings
      numeric_positions = torch.LongTensor(range(args.sequence_length+1)).cuda().unsqueeze(1)
      numeric_embedded = positional_embeddings(numeric_positions)
      numeric_transformed = memory_mlp_inner_from_pos(numeric_embedded)
#      print(numeric_transformed.size(), embedded_everything.size())

      # Retention probabilities
      memory_hidden = torch.log(1+torch.exp(memory_mlp_outer(relu(numeric_transformed + memory_mlp_inner(embedded_everything)))))
#      print(memory_hidden, memory_hidden.size())
      uniform_samples = torch.cuda.FloatTensor(1+args.sequence_length, args.batchSize).uniform_()
 #     print(uniform_samples)
      kuma_sample = torch.pow(1-torch.pow((1-uniform_samples), 1/memory_hidden[:,:,1]), 1/memory_hidden[:,:,0])
  #    print(kuma_sample)
      l,r=-0.1, 1.1
      stretched_sample = l+(r-l)*kuma_sample
      stretched_sample = torch.clamp(stretched_sample, min=0, max=1)
#      print(stretched_sample)
 #     print(embedded_everything.size())
  #    print(word_embeddings.weight.size())
   #   print(stretched_sample.size(), embedded_everything.size(), word_embeddings.weight[0].view(1,1,-1).size())
      embedded_noised = stretched_sample.unsqueeze(2) * embedded_everything + (1-stretched_sample.unsqueeze(2)) * word_embeddings.weight[0].view(1,1,-1)
#      print(embedded_noised.size())
      expectedNonzeros = (torch.pow(1-torch.pow( -l/(r-l)   , memory_hidden[:,:,0]), memory_hidden[:,:,1]))
 #     print(expectedNonzeros)
  #    print(expectedNonzeros.size())

      # Baseline predictions for prediction loss
#      baselineValues = 10*sigmoid(perword_baseline_outer(relu(perword_baseline_inner(embedded_everything[-1].detach()))))

      # Target
      target_tensor = Variable(numeric[1:], requires_grad=False)

      embedded = embedded_noised
      if TRAIN_LM and False:
         embedded = char_dropout(embedded)
         mask = bernoulli_input.sample()
         mask = mask.view(1, args.batchSize, 2*args.word_embedding_size)
         embedded = embedded * mask

      out, hidden = rnn_drop(embedded, hidden)

      # Only aim to predict the last word
      out = out[-1:]

      if TRAIN_LM and False:
        mask = bernoulli_output.sample()
        mask = mask.view(1, args.batchSize, args.hidden_dim)
        out = out * mask



      logits = output(out) 
      log_probs = logsoftmax(logits)

      # Prediction Loss 
      lossTensor = print_loss(log_probs.view(-1, len(itos)+3), target_tensor[-1].view(-1)).view(-1, args.batchSize)

      # Reward, term 1
      negativeRewardsTerm1 = lossTensor.mean(dim=0)

      # Reward, term 2
      # Regularization towards lower retention rates
      negativeRewardsTerm2 = expectedNonzeros.mean(dim=0)

      # Overall Reward
#      print(negativeRewardsTerm1)
 #     print(negativeRewardsTerm2)
#      quit()
      negativeRewardsTerm = negativeRewardsTerm1 + args.RATE_WEIGHT * negativeRewardsTerm2

      loss = negativeRewardsTerm.mean()

      global runningAverageReward
      global expectedRetentionRate


      # Construct running averages
      factor = 0.9996 ** args.batchSize

      expectedRetentionRate = factor * expectedRetentionRate + (1-factor) * float(negativeRewardsTerm2.mean())

      global runningAverageBaselineDeviation
      global runningAveragePredictionLoss
      runningAveragePredictionLoss = factor * runningAveragePredictionLoss + (1-factor) * round(float(negativeRewardsTerm1.mean()),3)
      if printHere:
         losses = lossTensor.data.cpu().numpy()
         numericCPU = numeric.cpu().data.numpy()
         memory_hidden_CPU = stretched_sample[:,0].cpu().data.numpy()
         print(("NONE", itos_total[numericCPU[0][0]]))
         for i in range((args.sequence_length)):
            print((losses[0][0] if i == args.sequence_length-1 else None , itos_total[numericCPU[i+1][0]], memory_hidden_CPU[i+1]))
         print(losses)
#         quit()

         print("PREDICTION_LOSS", runningAveragePredictionLoss, "\tTERM2", round(float(negativeRewardsTerm2.mean()),3), "\tAVERAGE_RETENTION", expectedRetentionRate, "\tDEVIATION FROM BASELINE", runningAverageBaselineDeviation, "\tREWARD", runningAverageReward)
      if updatesCount % 5000 == 0:
         print(("PREDICTION_LOSS", runningAveragePredictionLoss, "\tTERM2", round(float(negativeRewardsTerm2.mean()),3), "\tAVERAGE_RETENTION", expectedRetentionRate, "\tDEVIATION FROM BASELINE", runningAverageBaselineDeviation, "\tREWARD", runningAverageReward), file=sys.stderr)

      #runningAveragePredictionLoss = 0.95 * runningAveragePredictionLoss + (1-0.95) * float(negativeRewardsTerm1.mean())
      runningAverageReward = factor * runningAverageReward + (1-factor) * float(negativeRewardsTerm.mean())

      return loss, target_tensor.view(-1).size()[0]

def backward(loss, printHere):
      optim_memory.zero_grad()
      optim_lm.zero_grad()

      if printHere:
         print(loss)
      loss.backward()
      torch.nn.utils.clip_grad_value_(parameters_memory_cached, 5.0) #, norm_type="inf")
      if TRAIN_LM:
         torch.nn.utils.clip_grad_value_(parameters_lm_cached, 5.0) #, norm_type="inf")
      optim_memory.step()
      optim_lm.step()


lossHasBeenBad = 0

import time

totalStartTime = time.time()

lastSaved = (None, None)
devLosses = []
updatesCount = 0

maxUpdates = 100000 if args.tuning == 1 else 10000000000

for epoch in range(1000):
   print(epoch)
   training_data = corpusIteratorWikiWords.training(args.language)
   print("Got data")
   training_chars = prepareDatasetChunks(training_data, train=True)



   rnn_drop.train(True)
   startTime = time.time()
   trainChars = 0
   counter = 0
   hidden, beginning = None, None
   if updatesCount >= maxUpdates:
     break
   while updatesCount <= maxUpdates:
      counter += 1
      updatesCount += 1
      if updatesCount % 10000 == 0:
         learning_rate = args.learning_rate * math.pow(args.lr_decay, int(updatesCount/10000))
         optim_memory = torch.optim.SGD(parameters_memory(), lr=learning_rate, momentum=args.momentum) # 0.02, 0.9
         optim_lm     = torch.optim.SGD(parameters_lm(), lr=learning_rate, momentum=0) # 0.02, 0.9
      try:
         numeric = next(training_chars)
      except StopIteration:
         break
      printHere = (counter % 50 == 0)
      loss, charCounts = forward(numeric, printHere=printHere, train=True)
      backward(loss, printHere)
      if lossHasBeenBad > 100:
          print("Loss exploding, has been bad for a while")
          print(loss)
          assert False
      trainChars += charCounts 
      if printHere:
          print(("Loss here", loss))
          print((epoch,counter, trainChars))
          print("Dev losses")
          print(devLosses)
          print("Words per sec "+str(trainChars/(time.time()-startTime)))
          print(learning_rate)
          print(lastSaved)
          print(__file__)
          print(args)

      if (time.time() - totalStartTime)/60 > 4000:
          print("Breaking early to get some result within 72 hours")
          totalStartTime = time.time()
          break

# #     break
#   rnn_drop.train(False)
#
#
#   dev_data = corpusIteratorWikiWords.dev(args.language)
#   print("Got data")
#   dev_chars = prepareDatasetChunks(dev_data, train=False)
#
#
#     
#   dev_loss = 0
#   dev_char_count = 0
#   counter = 0
#   hidden, beginning = None, None
#   while True:
#       counter += 1
#       try:
#          numeric = next(dev_chars)
#       except StopIteration:
#          break
#       printHere = (counter % 50 == 0)
#       loss, numberOfCharacters = forward(numeric, printHere=printHere, train=False)
#       dev_loss += numberOfCharacters * loss.cpu().data.numpy()
#       dev_char_count += numberOfCharacters
#   devLosses.append(dev_loss/dev_char_count)
#   print(devLosses)
##   quit()
#   #if args.save_to is not None:
# #     torch.save(dict([(name, module.state_dict()) for name, module in named_modules.items()]), MODELS_HOME+"/"+args.save_to+".pth.tar")
#
#   with open("/u/scr/mhahn/recursive-prd/memory-upper-neural-pos-only_recursive_words/estimates-"+args.language+"_"+__file__+"_model_"+str(args.myID)+"_"+model+".txt", "w") as outFile:
#       print(str(args), file=outFile)
#       print(" ".join([str(x) for x in devLosses]), file=outFile)
#
#   if len(devLosses) > 1 and devLosses[-1] > devLosses[-2]:
#      break
#
#   state = {"arguments" : str(args), "words" : itos, "components" : [c.state_dict() for c in modules]}
#   torch.save(state, "/u/scr/mhahn/CODEBOOKS/"+args.language+"_"+__file__+"_code_"+str(args.myID)+".txt")
#
#
#
#
#
#
#   learning_rate = args.learning_rate * math.pow(args.lr_decay, len(devLosses))
#   optim = torch.optim.SGD(parameters(), lr=learning_rate, momentum=0.0) # 0.02, 0.9




#      global runningAverageBaselineDeviation
#      global runningAveragePredictionLoss
#


with open("/u/scr/mhahn/reinforce-logs-predict/results/"+__file__+"_"+str(args.myID), "w") as outFile:
   print(args, file=outFile)
   print(runningAverageReward, file=outFile)
   print(expectedRetentionRate, file=outFile)
   print(runningAverageBaselineDeviation, file=outFile)
   print(runningAveragePredictionLoss, file=outFile)



