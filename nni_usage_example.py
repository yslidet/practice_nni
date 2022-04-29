# -*- coding: utf-8 -*-
"""NNI_usage_example

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16x87s8FGi21BDl2v_VSrwgdQ2w7fIfYA

REF: https://towardsdatascience.com/how-to-improve-any-ml-dl-performance-by-10-easily-90dbbd01a4b3
"""

#install packages
# !pip install nni
# !pip install --upgrade nni --ignore-installed

"""# MNIST Classification **without NNI**"""

import torch 
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor
import nni

def train(model, device, train_loader, loss_fn, optimiser):
  size = len(train_loader.dataset)
  model.train()
  
  for batch, (X,y) in enumerate(train_loader):
    X, y = X.to(device), y.to(device)

    #compute prediction error 
    pred = model(X)
    loss = loss_fn(pred,  y)

    #backpropagation 
    optimiser.zero_grad()
    loss.backward()
    optimiser.step()

    if batch %100 == 0:
        loss, current = loss.item(), batch * len(X)
        print (f"loss: {loss:>7f} [{current:>5d}/{size:>5d}]")

def test(model, device, loss_fn, test_loader):
  size = len(test_loader.dataset)
  num_batches = len(test_loader)
  model.eval()
  test_loss, correct = 0,0
  with torch.no_grad():
    for X, y in test_loader:
      X, y = X.to(device), y.to(device)
      pred = model(X)
      test_loss += loss_fn(pred, y).item()
      correct += (pred.argmax(1)==y).type(torch.float).sum().item()
  test_loss/=num_batches
  correct /= size 
  print(f"Test Error: \n Accuracy {(100*correct):>0.1f}%, Avg Loss: {test_loss:>8f} \n")
  return correct

def main(args):
  training_data = datasets.FashionMNIST(root="data", train=True, download=True,transform=ToTensor(),)
  testing_data = datasets.FashionMNIST(root="data", train=False, download=True,transform=ToTensor(),)

  train_dataloader = DataLoader(training_data,batch_size=args['batch_size'])
  test_dataloader = DataLoader(testing_data,batch_size = 64)

  device = "cuda" if torch.cuda.is_available() else "cpu"
  print(f"Using {device} device")

  #Define Model 
  class NeuralNetwork(nn.Module):
    def __init__(self, hidden_size1, hidden_size2 ):
      super(NeuralNetwork,self).__init__()
      self.flatten = nn.Flatten()
      self.linear_relu_stack = nn.Sequential(
          nn.Linear(28*28, hidden_size1),
          nn.ReLU(), 
          nn.Linear(hidden_size1, hidden_size2),
          nn.ReLU(),
          nn.Linear(hidden_size2,10)
      )
    def forward(self, x):
      x = self.flatten(x)
      logits = self.linear_relu_stack(x)
      return logits
  
  model = NeuralNetwork(hidden_size1=args['hidden_size1'],
                        hidden_size2=args['hidden_size2']).to(device)
  print(model)
  loss_fn = nn.CrossEntropyLoss()
  optimiser = torch.optim.SGD(model.parameters(), lr=args['lr'])

  for epoch in range(10):
    print(f'Epoch {epoch+1}\n ------------------------')
    train(model, device, train_dataloader, loss_fn, optimiser)
    test_acc = test(model, device, loss_fn, test_dataloader)
    print(test_acc)
  print(f'final accuracy:{test_acc}')

if __name__ == '__main__':
  params = {
      'batch_size':32,
      'hidden_size1':128,
      'hidden_size2':128,
      'lr':0.001,
      'momentum':0.5
  }
  main(params)

"""# Hyperparam Search with NNI

## STEP1. search.py
"""

from nni.experiment import Experiment
from pathlib import Path
import os, sys
import time

#%% add parent_dir
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(parent_dir)

params = {
    'batch_size':32,
    'hidden_size1':128,
    'hidden_size2':128,
    'lr':0.001,
    'momentum':0.5
}

search_space = {
    'batch_size':{'_type':'choice', '_value':[32, 64, 128, 256]},
    'hidden_size1':{'_type':'choice', '_value':[64, 128, 256, 512]},
    'hidden_size2':{'_type':'choice', '_value':[64, 128, 256, 512]},
    'lr':{'_type':'loguniform', '_value':[0.0001, 0.1]},
    'momentum':{'_type':'uniform','_value':[0 , 1]}
}

experiment = Experiment('local')
experiment.config.trial_code_directory = '.'
experiment.config.trial_command = 'python mnist_nni.py' # command to run the code 
experiment.config.search_space = search_space
experiment.config.tuner.name = 'TPE'
experiment.config.tuner.class_args['optimize_mode'] = 'maximize'
experiment.config.max_trial_number = 30                 # number of experiments to run. In general, TPE requires min 20 trials to warm up.
experiment.config.trial_gpu_number = 0                  # CUDA is required when it’s greater than zero.
experiment.config.trial_concurrency = 2
experiment.run(8082)

input ('Press Enter to Quit')
experiment.stop()



