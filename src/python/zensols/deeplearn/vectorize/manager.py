from __future__ import annotations
"""Vectorization base classes and basic functionality.

"""
__author__ = 'Paul Landes'

from typing import Tuple, Any, Set, Dict, List
from dataclasses import dataclass, field
from abc import abstractmethod, ABCMeta
import logging
import sys
from itertools import chain
import collections
from io import TextIOBase
from torch import Tensor
from zensols.persist import persisted, PersistableContainer
from zensols.config import Writable, Writeback, ConfigFactory
from zensols.deeplearn import TorchConfig
from . import (
    NullFeatureContext,
    VectorizerError,
    FeatureVectorizer,
    FeatureContext,
    TensorFeatureContext,
    SparseTensorFeatureContext,
)

logger = logging.getLogger(__name__)


@dataclass
class EncodableFeatureVectorizer(FeatureVectorizer, metaclass=ABCMeta):
    """This vectorizer splits transformation up in to encoding and decoding.  The
    encoded state as a ``FeatureContext``, in cases where encoding is
    prohibitively expensive, is computed once and pickled to the file system.
    It is then loaded and finally decoded into a tensor.

    Examples include computing an encoding as indexes of a word embedding
    during the encoding phase.  Then generating the full embedding layer during
    decoding.  Note that this decoding is done with a ``TorchConfig`` so the
    output tensor goes directly to the GPU.

    This abstract base class only needs the ``_encode`` method overridden.  The
    ``_decode`` must be overridden if the context is not of type
    ``TensorFeatureContext``.

    """
    manager: FeatureVectorizerManager = field()
    """The manager used to create this vectorizer that has resources needed to
    encode and decode.

    """

    def transform(self, data: Any) -> Tensor:
        """Use the output of the encoding as input to the decoding to directly produce
        the output tensor ready to be used in testing, training, validation
        etc.

        """
        context = self.encode(data)
        return self.decode(context)

    def encode(self, data: Any) -> FeatureContext:
        """Encode data to a context ready to (potentially) be pickled.

        """
        return self._encode(data)

    def decode(self, context: FeatureContext) -> Tensor:
        """Decode a (potentially) unpickled context and return a tensor using the
        manager's :obj:`torch_config`.

        """
        self._validate_context(context)
        return self._decode(context)

    @property
    def torch_config(self) -> TorchConfig:
        """The torch configuration used to create encoded/decoded tensors.

        """
        return self.manager.torch_config

    @abstractmethod
    def _encode(self, data: Any) -> FeatureContext:
        pass

    def _decode(self, context: FeatureContext) -> Tensor:
        arr: Tensor
        if isinstance(context, NullFeatureContext):
            arr = None
        elif isinstance(context, TensorFeatureContext):
            arr = context.tensor
        elif isinstance(context, SparseTensorFeatureContext):
            arr = context.to_tensor(self.manager.torch_config)
        else:
            cstr = str(context) if context is None else context.__class__
            raise VectorizerError(f'unknown context: {cstr}')
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'decoded {type(context)} to {arr.shape}')
        return arr

    def _validate_context(self, context: FeatureContext):
        if context.feature_id != self.feature_id:
            raise VectorizerError(f'context meant for {context.feature_id} ' +
                                  f'routed to {self.feature_id}')


@dataclass
class TransformableFeatureVectorizer(EncodableFeatureVectorizer,
                                     metaclass=ABCMeta):
    """Instances of this class use the output of
    :meth:`.EncodableFeatureVectorizer.transform` (chain encode and decode) as
    the output of :meth:`EncodableFeatureVectorizer.encode`, then passes
    through the decode.

    This is useful if the decoding phase is very expensive and you'd rather
    take that hit when creating batches written to the file system.

    """
    encode_transformed: bool = field()
    """If ``True``, enable the transformed output of the encoding step as the
    decode step (see class docs).

    """

    def encode(self, data: Any) -> FeatureContext:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'encoding {type(data)}, also decode after encode' +
                         f'{self.encode_transformed}')
        if self.encode_transformed:
            ctx: FeatureContext = self._encode(data)
            arr: Tensor = self._decode(ctx)
            ctx = TensorFeatureContext(ctx.feature_id, arr)
        else:
            ctx = super().encode(data)
        return ctx

    def decode(self, context: FeatureContext) -> Tensor:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'decoding {type(context)}, already decoded: ' +
                         f'{self.encode_transformed}')
        if self.encode_transformed:
            ctx: TensorFeatureContext = context
            arr = ctx.tensor
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'already decoded: {arr.shape}')
        else:
            arr = super().decode(context)
        return arr


# manager
@dataclass
class FeatureVectorizerManager(Writeback, PersistableContainer, Writable):
    """Creates and manages instances of :class:`.EncodableFeatureVectorizer` and
    parses text in to feature based document.

    This handles encoding data into a context, which is data ready to be
    pickled on the file system with the idea this intermediate state is
    expensive to create.  At training time, the context is brought back in to
    memory and efficiently decoded in to a tensor.

    This class keeps track of two kinds of vectorizers:
        * module: registered with ``register_vectorizer`` in Python modules
        * configured: registered at instance create time in
                      ``configured_vectorizers``

    :see: :class:`.EncodableFeatureVectorizer`

    """
    ATTR_EXP_META = ('torch_config', 'configured_vectorizers')
    MANAGER_SEP = '.'

    torch_config: TorchConfig = field()
    """The torch configuration used to encode and decode tensors."""

    configured_vectorizers: Set[str] = field()
    """Configuration names of vectorizors to use by this manager."""

    def __post_init__(self):
        PersistableContainer.__init__(self)
        self.manager_set = None

    def transform(self, data: Any) -> \
            Tuple[Tensor, EncodableFeatureVectorizer]:
        """Return a tuple of duples with the output tensor of a vectorizer and the
        vectorizer that created the output.  Every vectorizer listed in
        ``feature_ids`` is used.

        """
        return tuple(map(lambda vec: (vec.transform(data), vec),
                         self.vectorizers.values()))

    @property
    @persisted('_vectorizers')
    def vectorizers(self) -> Dict[str, FeatureVectorizer]:
        """Return a dictionary of all registered vectorizers.  This includes both
        module and configured vectorizers.  The keys are the ``feature_id``s
        and values are the contained vectorizers.

        """
        return self._create_vectorizers()

    def _create_vectorizers(self) -> Dict[str, FeatureVectorizer]:
        vectorizers = collections.OrderedDict()
        feature_ids = set()
        conf_instances = {}
        if self.configured_vectorizers is not None:
            for sec in self.configured_vectorizers:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'creating vectorizer {sec}')
                if sec.find(self.MANAGER_SEP) >= 0:
                    raise VectorizerError(
                        f'Separator {self.MANAGER_SEP} not ' +
                        f'allowed in names: {sec}')
                vec = self.config_factory(sec, manager=self)
                conf_instances[vec.feature_id] = vec
                feature_ids.add(vec.feature_id)
        for feature_id in sorted(feature_ids):
            inst = conf_instances.get(feature_id)
            vectorizers[feature_id] = inst
        return vectorizers

    @property
    @persisted('_feature_ids')
    def feature_ids(self) -> Set[str]:
        """Get the feature ids supported by this manager, which are the keys of the
        vectorizer.

        :see: :meth:`.FeatureVectorizerManager.vectorizers`

        """
        return set(self.vectorizers.keys())

    def get(self, name: str) -> FeatureVectorizer:
        """Return the feature vectorizer named ``name``."""
        fv = self.vectorizers.get(name)
        # if we can't find the vectorizer, try using dot syntax to find it in
        # the parent manager set
        if name is not None and fv is None:
            idx = name.find(self.MANAGER_SEP)
            if self.manager_set is not None and idx > 0:
                mng_name, vec = name[:idx], name[idx+1:]
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'looking up {mng_name}:{vec}')
                mng = self.manager_set.get(mng_name)
                if mng is not None:
                    fv = mng.vectorizers.get(vec)
        return fv

    def __getitem__(self, name: str) -> FeatureVectorizer:
        fv = self.get(name)
        if fv is None:
            raise VectorizerError(
                f"Manager '{self}' has no vectorizer: '{name}'")
        return fv

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(str(self), depth, writer)
        for vec in self.vectorizers.values():
            vec.write(depth + 1, writer)


@dataclass
class FeatureVectorizerManagerSet(Writable, PersistableContainer):
    """A set of managers used collectively to encode and decode a series of
    features across many different kinds of data (i.e. labels, language
    features, numeric).

    """
    ATTR_EXP_META = ('managers',)
    name: str
    config_factory: ConfigFactory = field(repr=False)
    names: List[str]

    def __post_init__(self):
        super().__init__()

    @property
    @persisted('_managers')
    def managers(self) -> Dict[str, FeatureVectorizerManager]:
        """All registered vectorizer managers of the manager."""
        mngs = {}
        for n in self.names:
            f = self.config_factory(n)
            f.manager_set = self
            mngs[n] = f
        return mngs

    @property
    @persisted('_feature_ids')
    def feature_ids(self) -> Set[str]:
        """Return all feature IDs supported across all manager registered with the
        manager set.

        """
        return set(chain.from_iterable(
            map(lambda m: m.feature_ids, self.values())))

    def __getitem__(self, name: str) -> FeatureVectorizerManager:
        return self.managers[name]

    def get(self, name: str) -> FeatureVectorizerManager:
        return self.managers.get(name)

    def values(self) -> List[FeatureVectorizerManager]:
        return self.managers.values()

    def keys(self) -> Set[str]:
        return set(self.managers.keys())

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'{self.name}', depth, writer)
        for mng in self.managers.values():
            mng.write(depth + 1, writer)
