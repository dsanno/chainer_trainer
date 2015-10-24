import numpy as np
import six
import chainer
import chainer.functions as F
from chainer import optimizers
from chainer import cuda
from chainer.cuda import cupy

class Trainer(object):
    @classmethod
    def train(self, model, x, y, epoch, x_test=None, y_test=None, batch_size=100, loss_func=F.softmax_cross_entropy, optimizer=None, gpu_device=None):
        if gpu_device is None:
            model.to_cpu()
        else:
            model.to_gpu(gpu_device)
        if optimizer is None:
            optimizer = optimizers.Adam()
        optimizer.setup(model)
        with cupy.cuda.Device(gpu_device):
            for i in six.moves.range(1, epoch + 1):
                print 'epoch: {}'.format(i)
                loss, accuracy = Trainer.train_one(model, x, y, batch_size, optimizer=optimizer, loss_func=loss_func, gpu_device=gpu_device)
                print('train mean loss={}, accuracy={}'.format(loss, accuracy))
                if x_test is not None and y_test is not None:
                    loss, accuracy = Trainer.train_one(model, x_test, y_test, batch_size, loss_func=loss_func, gpu_device=gpu_device)
                    print('test mean loss={}, accuracy={}'.format(loss, accuracy))

    @classmethod
    def train_one(self, model, x, y, batch_size, optimizer=None, loss_func=F.softmax_cross_entropy, gpu_device=None):
        train = optimizer is not None and loss_func is not None
        total_size = len(x)
        assert total_size == len(y)
        if gpu_device is None:
            xp = np
        else:
            xp = cuda.cupy
        print xp.__name__
        perm = np.random.permutation(total_size)
        sum_loss = 0
        sum_accuracy = 0
        for i in six.moves.range(0, total_size, batch_size):
            x_batch = chainer.Variable(xp.asarray(x[perm[i:i + batch_size]]))
            y_batch = chainer.Variable(xp.asarray(y[perm[i:i + batch_size]]))
            if train:
                optimizer.zero_grads()
            y_out = model.forward(x_batch, train=train)
            loss = loss_func(y_out, y_batch)
            if train:
                loss.backward()
                optimizer.update()
            sum_loss += float(loss.data) * batch_size
            sum_accuracy += float(F.accuracy(y_out, y_batch).data) * batch_size
        return (sum_loss / total_size, sum_accuracy / total_size)