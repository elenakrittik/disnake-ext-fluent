# SPDX-License-Identifier: LGPL-3.0-only

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from disnake import Locale, LocalizationKeyError, LocalizationProtocol, LocalizationWarning
from fluent.runtime import FluentLocalization as FluentLocalizator
from fluent.runtime import FluentResourceLoader

from .utils import search_ftl_files, search_languages

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from .types import FluentFunction, PathT, ReturnT

__all__ = ("FluentStore",)
logger = logging.getLogger(__name__)


class FluentStore(LocalizationProtocol):
    """:class:`disnake.LocalizationProtocol` implementation for Fluent.

    Attributes
    ----------
    CACHE_BY_DEFAULT: ClassVar[str]
        Controls the default value for ``cache`` in :meth:`.l10n`. Does not affect caching
        of "static-by-definition" keys like application commands' names/descriptions.
        Defaults to ``False``.

    Parameters
    ----------
    strict: bool
        If ``True``, the store will raise :exc:`disnake.LocalizationKeyError` if a key or
        locale is not found.
    default_language: str
        The "fallback" language to use if localization for the desired languages is not found.
        Defaults to ``"en-US"``.
    functions: dict[str, FluentFunction] | None
        Custom functions to expose to FTLs. Key is the name of the function as should be accessible
        from FTLs, value is any function that returns a :class:`FluentType`.

    .. versionadded:: 0.1.0
    """

    CACHE_BY_DEFAULT: ClassVar[bool] = False

    _strict: bool
    _default_language: str
    _langs: list[str]
    _loader: FluentResourceLoader | None
    _localizators: dict[str, FluentLocalizator]
    _localization_cache: dict[str, str]
    _disnake_localization_cache: dict[str, dict[str, str | None]]
    _functions: dict[str, FluentFunction[Any]] | None

    def __init__(
        self,
        *,
        strict: bool = False,
        default_language: str = "en-US",
        functions: dict[str, FluentFunction[ReturnT]] | None = None,
    ) -> None:
        self._strict = strict
        self._default_language = default_language
        self._functions = functions

        self._loader = None
        self._localizators = {}
        self._localization_cache = {}
        self._disnake_localization_cache = {}

        logger.info("FluentStore initialized.")

    def get(self, key: str) -> dict[str, str] | None:
        """Localization retriever for disnake. You should use :meth:`.l10n` instead.

        Parameters
        ----------
        key: str
            The lookup key.

        Raises
        ------
        :exc:`disnake.LocalizationKeyError`
            No localizations for the provided key were found.

        Returns
        -------
        dict[str, str] | None
            The localizations for the provided key.
            Returns ``None`` if no localizations could be found.
        """
        if not self._loader:
            raise RuntimeError("FluentStore was not initialized yet.")

        logger.debug("disnake requested localizations for key '%s'.", key)

        localizations: dict[str, str | None] | None = self._disnake_localization_cache.get(key)

        if not localizations:
            logger.debug("disnake cache miss for key '%s'.", key)

            localizations = {}

            for lang in self._langs:
                localizations[lang] = self.l10n(key, lang)

            self._disnake_localization_cache[key] = localizations

        return localizations  # type: ignore # disnake *does* support this

    def load(self, path: PathT) -> None:
        """Initialize all internal attributes.

        ``path`` must point to a directory structured as per Fluent's guidelines.

        Parameters
        ----------
        path: str | :class:`os.PathLike`
            The path to the Fluent localization directory to load.

        Raises
        ------
        :exc:`RuntimeError`
            The provided path is invalid or couldn't be loaded.
        """
        path = Path(path)

        if not path.is_dir():
            raise RuntimeError(f"Path '{path}' does not exist or is not a directory.")

        self._langs = search_languages(path)
        resources = search_ftl_files(path)

        logger.info("Setting up FluentStore.")
        logger.debug(
            "Constructing localizators for locales '%s' using resource '%s'.",
            self._langs,
            resources,
        )

        self._loader = FluentResourceLoader(str(path) + "/{locale}")

        for lang in self._langs:
            self._localizators[lang] = FluentLocalizator(
                [lang, self._default_language],
                resources,
                self._loader,
                functions=self._functions,
            )

    def l10n(
        self,
        key: str,
        locale: Locale | str,
        values: dict[str, Any] | None = None,
        *,
        cache: bool | None = None,
    ) -> str | None:
        """Localize a key into the specified locale using the specified values.

        Parameters
        ----------
        key: str
            The localization key.
        locale: :class:`Locale` | str
            The locale.
        values: dict | None
            The mapping of values (parameters) to expose to the localization.
        cache: bool | None
            Whether to cache the result. Generally, static strings should be cached, and
            dynamic (those using functions in particular, but sometimes also parametrized
            ones) should not.

        Raises
        ------
        :exc:`disnake.LocalizationKeyError`
            No localizations for the provided key were found.

        Returns
        -------
        str
            The localized string.
        """
        if not self._loader:
            raise RuntimeError("FluentStore was not initialized yet.")

        logger.debug("Localization requested for key '%s' and locale '%s'.", key, locale)

        cache = cache or FluentStore.CACHE_BY_DEFAULT
        cache_key = key + ":" + str(locale) + ":" + str(values)

        if cache:
            if cached := self._localization_cache.get(cache_key):
                return cached

            logger.debug("Regular cache miss for key '%s' and locale '%s'.", key, locale)

        localizator = self._localizators.get(str(locale))

        if not localizator:
            warnings.warn(f"Localizator not found for locale '{locale!s}'.", LocalizationWarning)
            return None

        values = values or {}

        localized = localizator.format_value(key, values)

        if localized != key:  # translation *was* found
            if cache:
                self._localization_cache[cache_key] = localized
            return localized

        # translation was *not* found

        if self._strict:
            raise LocalizationKeyError(f"Key '{key}' not found for locale '{locale!s}'.")

        warnings.warn(f"Key '{key}' not found for locale '{locale!s}'.", LocalizationWarning)

        return None

    def reload(self) -> None:
        """Clear localizations and reload all previously loaded FTLs again.

        If an exception occurs, the previous data gets restored and the exception is re-raised.
        See :func:`.load` for possible raised exceptions.

        Not implemented yet.
        """
        raise NotImplementedError
