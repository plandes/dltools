# Facade

A [ModelFacade] wraps all [ModelExecutor] (see the [model](model.md)
documentation).  This class provides easy to use client entry points to the
model executor, which trains, validates, tests, saves and loads the model.  The
facade also proxies the more important functionality/access to the executor
and/or the network and model settings (i.e. epochs, learning rate etc).

Typically the [ModelFacade] is extended to customize your model.  This is
usually at least (if nothing else) to configure the packages you want to turn
logging on for debugging and for console output.  For example, for our Iris
example, we have the following as given in the [Create the model facade] cell
of the [Iris notebook] example:
```python
from dataclasses import dataclass
from zensols.deeplearn.model import ModelFacade

@dataclass
class IrisModelFacade(ModelFacade):
    def _configure_debug_logging(self):
        super()._configure_debug_logging()
        logging.getLogger('iris.model').setLevel(logging.DEBUG)

    def _configure_cli_logging(self, info_loggers: List[str],
                               debug_loggers: List[str]):
        super()._configure_cli_logging(info_loggers, debug_loggers)
        info_loggers.extend(['iris'])
```

If you extend the [ModelFacade] class, you can also put any special handling.
For example the [NLP ModelFacade] handles re-setting the word embedding input
layer by setting it as a string.


## Resources

The facade manages all resources of the [ModelExecutor], which is another
reason to use a facade over the executor directly.  Both classes have a
`deallocate` method that needs to be called when the object instances are no
longer used.  You can use the `dealloc` API that calls this in a `try`/`except`
like block automatically with:
```python
from zensols.config import ExtendedInterpolationEnvConfig as AppConfig
from zensols.persist import dealloc


def create_facade(*args, **kwargs) -> IrisModelFacade:
    config = AppConfig('test-resources/iris/iris.conf', env={'app_root': '.'})
    return IrisModelFacade(config, *args, **kwargs)


with dealloc(lambda: create_facade(False)) as facade:
    facade.configure_default_cli_logging()
    facade.epochs = 10
    facade.train()
    facade.test()
    facade.write_result()
    facade.persist_result()
```
The following happens in this example:
1. Create an [application context] and import factory.
1. Configure the facade for command line based logging (i.e. no training
   progress based scroll bar).
1. Set the number of epochs to train the model to `10`.
1. Train, validate and test the model.
1. Print and store the results of the train, validation and test phase.
1. De-allocate all resources in the facade and everything owned by the facade,
   including the executor and [ImportConfigFactory].

The de-allocation of resources traverses the object graph.  However, the most
important memory consuming items are GPU memory mini-batches.  This is
important when loading all batches directly to the GPU memory.


## Debugging the Model

A feature of the framework is *debugging* the model, which includes debug level
logging and reloads the module for a quick debug/test cycle while in the Python
REPL.  The facade provides access to this as well:
```python
with dealloc(lambda: create_facade(False)) as facade:
    facade.debug()
```
The output includes not only the details of tensor operation of each API based
layer, it also includes the [batch metadata], which is useful to find
[vectorized] data previously encoded.  See the [debugging notebook] for an
example of this debugging output.


<!-- links -->
[Iris notebook]: https://github.com/plandes/deeplearn/blob/master/notebook/iris.ipynb
[NLP ModelFacade]: https://plandes.github.io/deepnlp/api/zensols.deepnlp.model.html#zensols.deepnlp.model.facade.ModelFacade
[application context]: https://plandes.github.io/util/doc/config.html#application-context
[ImportConfigFactory]: https://plandes.github.io/util/api/zensols.config.html#zensols.config.factory.ImportConfigFactory
[debugging notebook]: https://github.com/plandes/deeplearn/tree/master/notebook/debug.ipynb

[vectorized]: preprocess.html#vectorizers
[batch metadata]: model.html#network-model
[ModelFacade]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.facade.ModelFacade
[ModelExecutor]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.executor.ModelExecutor
