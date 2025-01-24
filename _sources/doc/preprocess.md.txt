# Pre-Processing Data

Processing the raw data in your application's data set to creation of the
batches is a pre-process set that happens before the model is trained.
Everything in [PyTorch] is done with tensors, so we first must be able to
process the data in to some numeric form.  The framework uses the [Stash]
instances to create and later retrieve data since they allow an easy way to
index all data points with a unique key.  After the data is processed across
each instance, all data is then vectorized in to *batches*, which contain a
grouping of data and used as mini-batches.


## Configuration File

Please first read the [configuration factory] documentation as they are tightly
integrated with this framework.  We'll start our configuration file with
defining locations of the data set, where to store temporary and result files:
```ini
[default]
root_dir = ${env:app_root}
test_resources = ${root_dir}/test-resources/iris
temporary_dir = ${root_dir}/target/iris
temporary_batch_dir = ${temporary_dir}/batch
results_dir = ${temporary_dir}/results
```

Next we'll add two instances of a [TorchConfig], which help with allocating
[PyTorch] resources:
```ini
[torch_config]
class_name = zensols.deeplearn.TorchConfig
use_gpu = False
data_type = eval({'import': ['torch']}): torch.float32

[gpu_torch_config]
class_name = zensols.deeplearn.TorchConfig
use_gpu = True
data_type = eval({'import': ['torch']}): torch.float32
```
which defines a CPU based configuration used for creating
batches.  The GPU based configuration will be used for creating tensors in the
GPU device.  Both default to creating tensors of type 32-bit floats.


## Data as a Pandas Data Frame

The [Iris example] dataset comes as a CSV file, so we can use the framework's
[Pandas] class [DefaultDataframeStash], which we can use to create instances of
[DataPoint] directly:
```ini
[dataset_stash]
class_name = zensols.dataframe.DefaultDataframeStash
dataframe_path = path: ${default:temporary_dir}/df.dat
key_path = path: ${default:temporary_dir}/keys.dat
split_col = ds_type
input_csv_path = path: ${default:test_resources}/iris.csv
```
This creates an [Stash] instance that pre-processes data from a CSV file found
at `input_csv_path` in a ready to use format and pickles it in a file at
`dataframe_path`, which we've defined to be in our temporary file space as a
file system level caching strategy.  If the directory doesn't exist, it will
create it.

The [DefaultDataframeStash] needs a column to indicate to which data set the
respective point belongs.  A column called `ds_type` was added to [Iris data
set] in this repository for this reason.  The `split_col` is given this column
to create a set of keys for each data set for fast retrieval and access.  The
key splits (list of keys for each split) are pickled in the `key_path`

Next we create a [Stash] that create a new and separate stash for each data
set:
```ini
[dataset_split_stash]
class_name = zensols.dataset.DatasetSplitStash
delegate = instance: dataset_stash
split_container = instance: dataset_stash
```

The [DatasetSplitStash] has a [splits method] that returns a dictionary of
string split name to data set based on the key splits we defined earlier.  In
this case, we set both the `delegate`, which is the stash to use the data, and
the `split_container` as the [SplitStashContainer] since
[DefaultDataframeStash] serves both these purposes.  Note that for non-data
frame containers, this step of defining the resources need to be configured
with care.

Now let's access the data and test the data set split behavior:
```python
>>> from zensols.config import ExtendedInterpolationEnvConfig as AppConfig
>>> from zensols.config import ImportConfigFactory
>>> config = AppConfig('test-resources/iris/iris.conf', env={'app_root': '.'})
>>> fac = ImportConfigFactory(config)
>>> stash = fac('dataset_split_stash')
>>> len(stash)
150
>>> train = stash.splits['train']
>>> len(train)
113
>>> len(stash.splits['dev'])
12
>>> len(stash.splits['test'])
25
>>> stash.splits['dev'].keys()
('32', '34', '60', '80', '82', '124', '127', '129', '130', '136', '143', '144')
>>> row = next(stash.values())
<class 'pandas.core.series.Series'>
>>> row
sepal_length       5.2
sepal_width        4.1
petal_length       1.5
petal_width        0.1
species         setosa
ds_type            dev
Name: 32, dtype: object
>>>
```

## Vectorizers

Vectorizers are classes that transform a specific kind of data to a [PyTorch]
tensor.  The [FeatureVectorizer] is a base class that provides the `transform`
method and is used for transform only use cases (much like the fit/transform in
the [scikit-learn] package).  However, an extension is the
[EncodableFeatureVectorizer], which transforms as a two step process:
* encoding: outputs an intermediate picklable format,
* decoding: transforms the output of the encoding as a tensor.

As we'll see later, vectorizers are used to encode data in a compact format
that is quick to read and pickled to the file system for each data set.  During
training, this data is read back from the file system and transformed in to
tensors, usually going straight to the GPU.  In many cases, the tensors are
persisted directly to the file system, but this is up to the discretion of the
vectorizer.

Each vectorizer is configured as being a member of a vectorizer manager, and
vectorizer managers are configured in vectorizer manager sets.  The class
itself is vectorized and typically a member of its own vectorizer manager with
the features each a separate vectorizer manager.  For the Iris application, we
have the following label vectorizer:
```ini
[label_vectorizer]
class_name = zensols.deeplearn.vectorize.OneHotEncodedEncodableFeatureVectorizer
categories = eval: ['setosa', 'versicolor', 'virginica']
feature_id = ilabel
```
which provides a vectorizer that outputs one-hot encoded vectors for the three
types of Iris flowers.  When creating batches, the output shape will be
`(batches, 1)`.  Next we create a vectorizer that decodes features
directly from the row features of the data frame:
```ini
[series_vectorizer]
class_name = zensols.deeplearn.vectorize.SeriesEncodableFeatureVectorizer
feature_id = iseries
```

Finally we create the vectorizer manager and the set it belongs to:
```ini
[iris_vectorizer_manager]
class_name = zensols.deeplearn.vectorize.FeatureVectorizerManager
torch_config = instance: torch_config
configured_vectorizers = eval: 'label_vectorizer series_vectorizer'.split()

[vectorizer_manager_set]
class_name = zensols.deeplearn.vectorize.FeatureVectorizerManagerSet
names = eval: 'iris_vectorizer_manager'.split()
```
where we provide the CPU based `torch_config` used to generate the encoded
tensors when persisting to the file system.  Given our application is so
simple, we use only one vectorizer manager for labels and features.

See the documentation on the [list of vectorizers](#vectorizers.md).


## Processing Data Points

Each observation is called a *data point* in the framework and extends from
[DataPoint].  Your application must extend this class and define properties and
attributes that access the data that is to be vectorized.

For the Iris example, the [IrisDataPoint] extends the [DataPoint] and contains
a [Pandas] row as we saw in the [previous
section](#data-as-a-pandas-data-frame).  We need to define a class that will be
instantiated for each data point [Pandas] row:
```python
@dataclass
class IrisDataPoint(DataPoint):
    LABEL_COL = 'species'
    FLOWER_DIMS = 'sepal_length sepal_width petal_length petal_width'.split()

    row: pd.Series

    @property
    def label(self) -> str:
        return self.row[self.LABEL_COL]

    @property
    def flower_dims(self) -> pd.Series:
        return [self.row[self.FLOWER_DIMS]]
```


## Batches

During training, [PyTorch] takes mini-batches of data that are groupings of
occurrences, or *data points*, which are grouped in to [Batch] instances.  This
class is responsible for using the vectorizers to encode the data that's
pickled to the file system, then read it back and decode it.

A [BatchStash] is a [Stash] that manages instances of [Batches], which includes
creating them (when not already found on the file system).  Because
[BatchStash] extends from [MultiProcessStash], this is done across multiple sub
processes to speed the work up.  By default, the configuration of worker
processes are based on the number of cores in the system.

Like the [DataPoint], you're application needs to extend from [Batch] with data
properties.  For the Iris example, we define:
```python
@dataclass
class IrisBatch(Batch):
    MAPPINGS = BatchFeatureMapping(
        'label',
        [ManagerFeatureMapping(
            'iris_vectorizer_manager',
            (FieldFeatureMapping('label', 'ilabel', True),
             FieldFeatureMapping('flower_dims', 'iseries')))])

    def _get_batch_feature_mappings(self) -> BatchFeatureMapping:
        return self.MAPPINGS

    def get_flower_dimensions(self) -> torch.Tensor:
        return self.attributes['flower_dims']
```
The class defines an access method for the features in `get_flower_dimensions`.
It also defines a metadata mapping.  The `label` string indicates this is the
attribute name in the batch for labels.  The vectorizer manager for features
and labels is then given with mappings from attribute name to feature ID.  The
`True` in the label field mapping indicates it is an aggregate and to use the
vectorizer on each item in the list, then concatenate the result in to one tensor.

First let's define how and where to store the batches as a [Stash]:
```ini
[batch_dataset_dir_stash]
class_name = zensols.persist.DirectoryStash
path = path: ${default:temporary_batch_dir}/data
```
This uses a directory stash that will pickle each batch as a separate file in
the temporary space `data` directory specified.


## Batch Stash

Next we configure the [BatchStash], which is responsible for creating each data
point row from the [Pandas] data frame, then [vectorizing](#vectorizers) it.
```ini
[batch_dataset_stash]
class_name = zensols.deeplearn.batch.BatchStash
delegate = instance: batch_dataset_dir_stash
split_stash_container = instance: dataset_stash
data_point_id_sets_path = path: ${default:temporary_batch_dir}/batch-point-keys.dat
vectorizer_manager_set = instance: vectorizer_manager_set
data_point_type = eval({'import': ['iris.model']}): iris.model.IrisDataPoint
batch_type = eval({'import': ['iris.model']}): iris.model.IrisBatch
decoded_attributes = None
model_torch_config = instance: gpu_torch_config
chunk_size = 0
workers = 0
batch_size = 20
batch_limit = eval: sys.maxsize
```
There is a lot to unpack in this configuration, so the parameters (options)
broken down below:
* `delegate`: we refer to the directory stash for backing persistence of the
  batches
* `split_stash_container`: we'll reuse the same key splits from the data frame
  based stash
* `data_point_id_sets_path`: tells where to store the generated mapping of
  *batch* to *data point* keys, which tell us which data points will be encoded
  in to each batch
* `vectorizer_manager_set`: refers to the vectorizer set we defined
  [previously](#vectorizers)
* `data_point_type`: is a class [we defined](#processing-data-points), which is
  the class that is given the row data in the initializer
* `batch_type`: is the class of the batch, which we defined in the
  [batches](#batches) section.
* `decoded_attributes`: a list of feature attributes (i.e. `label` or
  `flower_dims`) to fetch from the batch.  If `None` is given, all are used,
  which is our case.  Identifying only certain features can speed up batch
  reads from the file system by leaving out those not needed for the model.
* `model_torch_config`: is the instance of the [TorchConfig] to use to decode,
  which has to be in sync with model (this instance reference will pop up other
  places as well)
* `chunk_size`: the number of chunks for each process or `0` to optimize (see
  [MultiProcessStash])
* `workers`: the number of worker processes or `0` to optimize (see [MultiProcessStash])
* `batch_size`: the max number of data points for each batch
* `batch_limit`: the max number of batches to create (handy for debugging).

When you first use the [BatchStash] instance, it will look to see if the
directory specified in the `batch_dataset_dir_stash` stash exists.  When it
finds it will not, it will spawn multiple processes each created a set of
batches on the file system.  Let's explore what's in the batch we defined:
```python
>>> from zensols.config import ExtendedInterpolationEnvConfig as AppConfig
>>> from zensols.config import ImportConfigFactory
>>> config = AppConfig('test-resources/iris/iris.conf', env={'app_root': '.'})
>>> fac = ImportConfigFactory(config)
>>> stash = fac('batch_dataset_stash')
>>> tuple(stash.keys())
('7', '4', '0', '2', '3', '1', '5', '8', '6')
>>> batch = next(stash.values())
>>> len(batch)
20
>>> batch.write()
IrisBatch
    size: 20
        label: torch.Size([20, 3])
        flower_dims: torch.Size([20, 4])
>>> batch.keys()
('label', 'flower_dims')
>>> batch['label'].shape
torch.Size([20, 3])
>>> batch['flower_dims'].shape
torch.Size([20, 4])
>>> batch['label']
tensor([[0., 0., 1.],
        ...
        [0., 0., 1.]])
>>> batch['flower_dims']
tensor([[6.3000, 2.9000, 5.6000, 1.8000],
        ...
        [7.7000, 2.8000, 6.7000, 2.0000]])
```

Finally, we define a split stash as we did for the data frame based stash.
This is necessary so later the model trainer can produce a training, validation
and test data set to train and test the model.
```ini
[iris_dataset_stash]
class_name = zensols.dataset.SortedDatasetSplitStash
delegate = instance: batch_dataset_stash
split_container = instance: batch_dataset_stash
sort_function = eval: int
```

Here we define a [SortedDatasetSplitStash] instance to keep the data sorted.
In our case, it doesn't matter our data is already in a random order, so when
keys are assigned the order is maintained exactly as it was before.  This
guarantees that same order is kept.  We could have also used a
[DatasetSplitStash], which would still keep an order to the data, just not one
that returns the data in ascending order by key.

The [BatchStash] extends [SplitStashContainer] and delegates that functionality
to the `split_stash_container` instance.  For this reason, both the
`split_container` and `delegate` point to the same instance.  The
`sort_function` tells the stash to convert keys from strings (which are used as
keys in all stashes) before sorting.


<!-- links -->
[PyTorch]: https://pytorch.org
[Pandas]: https://pandas.pydata.org
[configuration factory]: https://plandes.github.io/util/doc/config.html#configuration-factory
[scikit-learn]: https://scikit-learn.org/stable/

[Iris data set]: https://archive.ics.uci.edu/ml/datasets/iris
[Iris example]: https://github.com/plandes/deeplearn/blob/master/test/python/iris/model.py
[Iris example configuration]: https://github.com/plandes/deeplearn/blob/master/test-resources/iris
[IrisDataPoint]: https://github.com/plandes/deeplearn/blob/master/test/python/iris/model.py

[Stash]: https://plandes.github.io/util/api/zensols.persist.html#zensols.persist.domain.Stash
[FeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.domain.FeatureVectorizer
[DataPoint]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.domain.DataPoint
[TorchConfig]: ../api/zensols.deeplearn.html#zensols.deeplearn.torchconfig.TorchConfig
[DefaultDataframeStash]: ../api/zensols.dataframe.html#zensols.dataframe.stash.DefaultDataframeStash
[DatasetSplitStash]: ../api/zensols.dataset.html#zensols.dataset.stash.DatasetSplitStash
[splits method]: ../api/zensols.dataset.html?highlight=datasetsplitstash#zensols.dataset.interface.SplitStashContainer.splits
[SplitStashContainer]: ../api/zensols.dataset.html#zensols.dataset.interface.SplitStashContainer
[FeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.domain.FeatureVectorizer
[BatchStash]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.stash.BatchStash
[EncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.manager.EncodableFeatureVectorizer
[Batch]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.domain.Batch
[MultiProcessStash]: https://plandes.github.io/util/api/zensols.multi.html#zensols.multi.stash.MultiProcessStash
[BatchFeatureMapping]: ../api/zensols.deeplearn.batch.html#zensols.deeplearn.batch.mapping.BatchFeatureMapping
[SortedDatasetSplitStash]: ../api/zensols.dataset.html#zensols.dataset.stash.SortedDatasetSplitStash
