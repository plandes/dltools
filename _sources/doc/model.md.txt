# Model

Please first read the [data pre-processing] documentation before proceeding.
In this document, the model for the [Iris example] is defined and we train and
test the model.

The model contains of two kinds of configuration and set up:
* network settings: configuration of the neural network itself, such as types
  and numbers of layers
* model settings: configuration of the model, such as the criterion, optimizer,
  and learning rate


## Class Name Parlance

Network models usually implement layers of a deep learning network.  To follow
the convention set by [PyTorch], the Python classes that implement the layers
are referred to as *modules* and don't carry the term *layer* in the class
name.

Given that the modules that implement layers in this framework typically
require a lot of configuration, a separate *settings* class is given to each
corresponding module implementation.  For example, a
[DeepLinearNetworkSettings] configures a [DeepLinear] layer.


## Network Settings

The network settings declares which network modules to use in the model.  The
network settings is a class that contains the configuration that tells the
module how to build itself, and what that module is.  In the [Iris example], we
first need to create the class:
```python
@dataclass
class IrisNetworkSettings(DeepLinearNetworkSettings):
    def get_module_class_name(self) -> str:
        return __name__ + '.IrisNetwork'
```

We only need to extend from [DeepLinearNetworkSettings], which already has all
the configuration we need since our model is a simple linear set of layers.
We'll define that configuration soon.  However, we must override the abstract
method `get_module_class_name`, which tells us what model to create at
train/test time.


### Configuring the Network Settings

The `IrisNetworkSettings` instance will be populated by the [ConfigFactory]
with fields inherited from [DeepLinearNetworkSettings]:
```ini
[net_settings]
class_name = iris.model.IrisNetworkSettings
dropout = 0.1
activation = None
middle_features = eval: [5, 1]
in_features = 4
out_features = 3
proportions = False
repeats = 1
batch_norm_d = None
batch_norm_features = None
```
which will create a deep linear network expecting 4 input features (one for
each row feature of the flower size data), with 5 times the number of features
in the second layer, same number of feature for the third layer, and finally an
output of three features--one for each flower type.  See
[DeepLinearNetworkSettings] for more details.


## Network Model

The [BaseNetworkModule] class provides additional debugging and logging
convenience methods.


### Debugging

The method `_debug` in the base class logs as debug to
the passed logger but also provides additional formatting indicating the name
of the model, which is taken from `MODULE_NAME`.  For a simple module like
this, it might seem unnecessary.  However, this additional information is
crucial in debugging large models.  The `_shape_debug` method logs the shape of
a tensor.


### Extending the Base Module

Finally, we provide an implementation of [BaseNetworkModule], which extends
from `torch.nn.Module`.
```python
class IrisNetwork(BaseNetworkModule):
    MODULE_NAME = 'iris'

    def __init__(self, net_settings: IrisNetworkSettings):
        super().__init__(net_settings, logger)
        self.fc = DeepLinear(net_settings)

    def deallocate(self):
        super().deallocate()
        self._deallocate_children_modules()

    def _forward(self, batch: Batch) -> Tensor:
        if self.logger.isEnabledFor(logging.DEBUG):
            self._debug(f'label shape: {batch.get_labels().shape}, ' +
                        f'{batch.get_labels().dtype}')

        x = batch.get_flower_dimensions()
        self._shape_debug('input', x)

        x = self.fc(x)
        self._shape_debug('linear', x)

        return x
```
Note that we pass our own logger to the base class, which is needed for the
aforementioned logging convenience methods and is set attribute `logger` in the
base class.  Another important difference is we provide a `deallocate` method
(see the [memory management section](#memory-management) for more information)
and a `_forward` method.  This private forward method now takes a batch object
instance that's been decoded by a [vectorizer].  The [Batch] object has the
vectorized tensors ready to be used, the labels, and [BatchMetadata].  The
[Batch] object get load the original [data point] objects with the
[get_data_points] method.


### Configuring the Network Model

In the initializer, all we need to do is create a [DeepLinear] module with the
configuration give from the [ConfigFactory] that was used to create the network
settings instance.

The model is configured as follows:
```ini
[model_settings]
class_name = zensols.deeplearn.ModelSettings
path = path: ${default:temporary_dir}/model
nominal_labels = False
learning_rate = 0.1
batch_iteration = gpu
epochs = 15
```
which creates a `ModelSettings` class used to create the model that stores the
model in the temporary directory under `model`.  The `nominal_labels` tell the
framework that the class is not an integer nominal index for each class.  this
is because the model outputs a three neuron output for each flower type (see
the [network model](#network-model) section).  The model will train for 15
epochs using a learning rate of 0.1 using the (default) `torch.nn.Adam`
optimizer with the (default) loss function `torch.nn.CrossEntropyLoss`.  See
[ModelSettings] documentation for more information.

The `batch_iteration = gpu` means the entire batch data set will be decoded in
to GPU memory (see the [training](#training) section).  See the [ModelSettings]
class for full documentation on each option.


## Executor

Finally we define the [ModelExecutor], which is the class that trains,
validates and tests the model:
```ini
[executor]
class_name = zensols.deeplearn.model.ModelExecutor
model_name = Iris
model_settings = instance: model_settings
net_settings = instance: net_settings
dataset_stash = instance: iris_dataset_stash
dataset_split_names = eval: 'train dev test'.split()
result_path = path: ${default:results_dir}
```

This creates an executor that uses the string `Iris` in all generated graphs
and result output.  It refers to the model and network settings we have already
defined.  It uses the `iris_dataset_stash` we defined in the
[preprocess](preprocess.md) documentation.

You can use the executor directly as demonstrated in the [Iris notebook] or
with a facade as shown in the [facade](facade.md) documentation.

During the training of the model, if the `update_path` path is configured on
the executor, the training and validation loss is [plotted].  This file also
informs the [ModelExecutor] of any changes while training by providing
configuration as a JSON file.  For example:
```json
{"epoch": 20}
```
resets the current epoch to `20` by the [TrainManager].  By doing this, you can
shorten or lengthen training time.  If the file exists, but is empty, or
otherwise cannot be parsed, the training is early stopped.


## Training

The [executor](#exectuor) is used to train, validation and test the model.
During the training phase, this includes:
1. Loading the batch(es) in memory.
1. Training the model with the training data set with auto gradients on for
   each epoch.
1. Using the validation data set to calculate the validation loss for each
   epoch.
1. Across each epoch, if and only if the validation loss is lower, the model is
   saved.
1. Add the validation loss and outcome of each data point to a [ModelResult].
1. If the validation loss has not decreased within the window set by the
   [ModelSettings] `max_consecutive_increased_count` parameter, then early stop
   training the model.
1. If the model has been trained on the number of `epochs` set in the
   [ModelSettings], then stop.
1. Otherwise, the learning rate is adjusted with a schedule based on the
   `scheduler_class_name` [ModelSettings] parameter and we iterate over another
   epoch.


### Memory Management

When the training process starts, batches are loaded in one of three ways:
* `gpu`, buffers all data in the GPU,
* `cpu`, which means keep all batches in CPU memory (the default), or
* `buffered` which means to buffer only one batch at a time (only
  for *very* large data).

When using the `gpu` setting, all batches (and thus all data) is loaded in to
GPU memory all at once.  This means the output of the decoding process detailed
in the [vectorizer] documentation.  If this parameter is set to `cpu`, all
batches would be decoded to CPU memory, then moved to the GPU for each epoch.
For the `buffered` setting, all batches are decoded for each epoch.

In order to keep a low memory profile, the Python garbage collector is called
at different intervals depending on the `gc_level` parameter in the
[ModelSettings].

See the [model section](#network-model) for more details on the model settings.


## Testing

The testing data set is loaded in the same way as the [training](#training)
data set.  In the same way, the outcome of each testing data point is stored in
[ModelResult] after being loaded from the file system saved from the training
phase.


<!-- links -->
[PyTorch]: https://pytorch.org

[Iris example]: https://github.com/plandes/deeplearn/blob/master/test/python/iris/model.py
[Iris notebook]: https://github.com/plandes/deeplearn/blob/master/notebook/iris.ipynb

[data pre-processing]: preprocess.md
[vectorizer]: preprocess.html#vectorizers
[data point]: preprocess.html#processing-data-points
[plotted]: results.html#plotting-loss

[DeepLinearNetworkSettings]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.linear.DeepLinearNetworkSettings
[DeepLinear]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.linear.DeepLinear
[BaseNetworkModule]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.module.BaseNetworkModule
[Batch]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.domain.Batch
[get_data_points]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.domain.Batch.get_data_points
[BatchMetadata]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.meta.BatchMetadata
[ConfigFactory]: https://plandes.github.io/util/api/zensols.config.html#zensols.config.factory.ConfigFactory
[ModelSettings]: ../api/zensols.deeplearn.html#zensols.deeplearn.domain.ModelSettings
[ModelExecutor]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.executor.ModelExecutor
[ModelResult]: ../api/zensols.deeplearn.result.html#zensols.deeplearn.result.domain.ModelResult
[TrainManager]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.trainmng.TrainManager
