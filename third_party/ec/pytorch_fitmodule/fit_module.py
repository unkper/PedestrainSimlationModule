import logging

import torch

from collections import OrderedDict
from functools import partial
from torch.autograd import Variable
from torch.nn import BCELoss, Module
from torch.optim import RAdam

from .utils import add_metrics_to_log, get_loader, log_to_message, ProgressBar, get_loader_r_training

DEFAULT_LOSS = BCELoss()


class FitModule(Module):

    def fit(self,
            X,
            y,
            batch_size=32,
            epochs=1,
            verbose=True,
            validation_split=0.,
            validation_data=None,
            shuffle=True,
            initial_epoch=0,
            seed=None,
            loss=DEFAULT_LOSS,
            optimizer=None,
            metrics=None):
        """Trains the model similar to Keras' .fit(...) method

        # Arguments
            X: training data Tensor.
            y: target data Tensor.
            batch_size: integer. Number of samples per gradient update.
            epochs: integer, the number of times to iterate
                over the training data arrays.
            verbose: 0, 1. Verbosity mode.
                0 = silent, 1 = verbose.
            validation_split: float between 0 and 1:
                fraction of the training data to be used as validation data.
                The model will set apart this fraction of the training data,
                will not train on it, and will evaluate
                the loss and any model metrics
                on this data at the end of each epoch.
            validation_data: (x_val, y_val) tuple on which to evaluate
                the loss and any model metrics
                at the end of each epoch. The model will not
                be trained on this data.
            shuffle: boolean, whether to shuffle the training data
                before each epoch.
            initial_epoch: epoch at which to start training
                (useful for resuming a previous training run)
            seed: random seed.
            optimizer: training optimizer
            loss: training loss
            metrics: list of functions with signatures `metric(y_true, y_pred)`
                where y_true and y_pred are both Tensors

        # Returns
            list of OrderedDicts with training metrics
        """
        # logging.warning(u"start training r-network!")
        if batch_size == 1:
            logging.error("batch-size equal to 1!")
        if seed and seed >= 0:
            torch.manual_seed(seed)
        # Prepare validation data
        if validation_data:
            X_val, y_val = validation_data
        elif validation_split and 0. < validation_split < 1.:
            split = int(X.size()[0] * (1. - validation_split))
            X, X_val = X[:split], X[split:]
            y, y_val = y[:split], y[split:]
        else:
            X_val, y_val = None, None
        # Build DataLoaders
        if not isinstance(X, list): # for r_training
            train_data = get_loader(X, y, batch_size, shuffle)
        else:
            X1, X2 = X
            train_data = get_loader_r_training(X1, X2, y, batch_size, shuffle)
        opt = optimizer
        # Run training loop
        logs = []
        total_loss = 0.0
        self.train()
        for t in range(initial_epoch, epochs):
            if verbose:
                print("Epoch {0} / {1}".format(t+1, epochs))
            # Setup logger
            if verbose:
                pb = ProgressBar(len(train_data))
            log = OrderedDict()
            epoch_loss = 0.0
            # Run batches
            for batch_i, batch_data in enumerate(train_data):
                # Get batch data
                if not isinstance(X, list):
                    X_batch = Variable(batch_data[0])
                    y_batch = Variable(batch_data[1])
                else:
                    X_batch = [Variable(batch_data[0]), Variable(batch_data[1])]
                    y_batch = Variable(torch.as_tensor(batch_data[2], device=self.device, dtype=torch.float32))
                # Backprop
                opt.zero_grad()
                if not isinstance(X_batch, list):
                    y_batch_pred = self(X_batch)
                else:
                    y_batch_pred = self(X_batch[0], X_batch[1])
                batch_loss = loss(y_batch_pred, y_batch)
                batch_loss.backward()
                opt.step()
                # Update status
                epoch_loss += batch_loss.data
                log['loss'] = float(epoch_loss) / (batch_i + 1)
                if verbose:
                    pb.bar(batch_i, log_to_message(log))
            self.eval()
            # Run metrics
            if metrics:
                y_train_pred = self.predict(X, batch_size)
                add_metrics_to_log(log, metrics, y, y_train_pred)
            # if X_val is not None and y_val is not None:
            #     y_val_pred = self.predict(X_val, batch_size)
            #     val_loss = loss(Variable(y_val_pred), Variable(torch.as_tensor(y_val, device=self.device, dtype=torch.float32)))
            #     log['val_loss'] = val_loss.data
            #     if metrics:
            #         add_metrics_to_log(log, metrics, y_val, y_val_pred, 'val_')
            logs.append(log)
            total_loss += epoch_loss
            if verbose:
                pb.close(log_to_message(log))
        #logging.warning(u"end training r-network!")
        return logs, total_loss / (epochs - initial_epoch)

    def predict(self, X, batch_size=32):
        """Generates output predictions for the input samples.

        Computation is done in batches.

        # Arguments
            X: input data Tensor.
            batch_size: integer.

        # Returns
            prediction Tensor.
        """
        # Build DataLoader
        if not isinstance(X, list):
            data = get_loader(X, batch_size=batch_size)
        else:
            X1, X2 = X
            data = get_loader_r_training(X1, X2, batch_size=batch_size)
        # Batch prediction
        self.eval()
        if not isinstance(X, list):
            r, n = 0, X.size()[0]
        else:
            r, n = 0, X1.size()[0]
        for batch_data in data:
            # Predict on batch
            if not isinstance(X, list):
                X_batch = Variable(batch_data[0])
                y_batch_pred = self(X_batch).data
            else:
                X_batch = [Variable(batch_data[0]), Variable(batch_data[1])]
                y_batch_pred = self(X_batch[0], X_batch[1]).data
            # Infer prediction shape
            if r == 0:
                y_pred = torch.zeros((n,) + y_batch_pred.size()[1:])
            # Add to prediction tensor
            y_pred[r : min(n, r + batch_size)] = y_batch_pred
            r += batch_size
        return y_pred
