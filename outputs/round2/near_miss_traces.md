# E.2 Claude near-miss traces

All Claude non-hit comments whose file matches an oracle file for the instance (N=30). Each block lists the comment, the nearest oracle hunk in the same file, and source context windows around both.

## Near-miss 1: claude-sonnet-4-5  /  django__django-11133

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `879cc3da6249e920b8d54518a0ae06de835d7373` |
| comment file (original) | `django/http/response.py` |
| comment file (normalised) | `django/http/response.py` |
| comment lines | 173-173 |
| nearest oracle site | `site-0001` |
| oracle file | `django/http/response.py` |
| oracle lines | 229-235 |
| distance (lines) | 56 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Should use datetime.datetime.utcnow() instead of expires.utcnow() which is invalid.

### Source context (±5 lines around comment range)

```
   168:         self.cookies[key] = value
   169:         if expires is not None:
   170:             if isinstance(expires, datetime.datetime):
   171:                 if timezone.is_aware(expires):
   172:                     expires = timezone.make_naive(expires, timezone.utc)
>  173:                 delta = expires - expires.utcnow()
   174:                 # Add one second so the date matches exactly (a fraction of
   175:                 # time gets lost between converting to a timedelta and
   176:                 # then the date string).
   177:                 delta = delta + datetime.timedelta(seconds=1)
   178:                 # Just set max_age - the max_age logic will set expires.
```

### Source context (±5 lines around oracle hunk)

```
   224:         """Turn a value into a bytestring encoded in the output charset."""
   225:         # Per PEP 3333, this response body must be bytes. To avoid returning
   226:         # an instance of a subclass, this function returns `bytes(value)`.
   227:         # This doesn't make a copy when `value` already contains bytes.
   228: 
>  229:         # Handle string types -- we can't rely on force_bytes here because:
>  230:         # - Python attempts str conversion first
>  231:         # - when self._charset != 'utf-8' it re-encodes the content
>  232:         if isinstance(value, bytes):
>  233:             return bytes(value)
>  234:         if isinstance(value, str):
>  235:             return bytes(value.encode(self.charset))
   236:         # Handle non-string types.
   237:         return str(value).encode(self.charset)
   238: 
   239:     # These methods partially implement the file-like object interface.
   240:     # See https://docs.python.org/library/io.html#io.IOBase
```

---

## Near-miss 2: claude-sonnet-4-5  /  django__django-11133

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `879cc3da6249e920b8d54518a0ae06de835d7373` |
| comment file (original) | `django/http/response.py` |
| comment file (normalised) | `django/http/response.py` |
| comment lines | 199-199 |
| nearest oracle site | `site-0001` |
| oracle file | `django/http/response.py` |
| oracle lines | 229-235 |
| distance (lines) | 30 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: samesite validation excludes 'none' which is a valid SameSite value.

### Source context (±5 lines around comment range)

```
   194:         if secure:
   195:             self.cookies[key]['secure'] = True
   196:         if httponly:
   197:             self.cookies[key]['httponly'] = True
   198:         if samesite:
>  199:             if samesite.lower() not in ('lax', 'strict'):
   200:                 raise ValueError('samesite must be "lax" or "strict".')
   201:             self.cookies[key]['samesite'] = samesite
   202: 
   203:     def setdefault(self, key, value):
   204:         """Set a header unless it has already been set."""
```

### Source context (±5 lines around oracle hunk)

```
   224:         """Turn a value into a bytestring encoded in the output charset."""
   225:         # Per PEP 3333, this response body must be bytes. To avoid returning
   226:         # an instance of a subclass, this function returns `bytes(value)`.
   227:         # This doesn't make a copy when `value` already contains bytes.
   228: 
>  229:         # Handle string types -- we can't rely on force_bytes here because:
>  230:         # - Python attempts str conversion first
>  231:         # - when self._charset != 'utf-8' it re-encodes the content
>  232:         if isinstance(value, bytes):
>  233:             return bytes(value)
>  234:         if isinstance(value, str):
>  235:             return bytes(value.encode(self.charset))
   236:         # Handle non-string types.
   237:         return str(value).encode(self.charset)
   238: 
   239:     # These methods partially implement the file-like object interface.
   240:     # See https://docs.python.org/library/io.html#io.IOBase
```

---

## Near-miss 3: claude-sonnet-4-5  /  django__django-11422

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `df46b329e0900e9e4dc1d60816c1dce6dfc1094e` |
| comment file (original) | `django/utils/autoreload.py` |
| comment file (normalised) | `django/utils/autoreload.py` |
| comment lines | 563-563 |
| nearest oracle site | `site-0001` |
| oracle file | `django/utils/autoreload.py` |
| oracle lines | 114-120 |
| distance (lines) | 443 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: setDaemon() is deprecated; use daemon property or daemon parameter in Thread constructor instead.

### Source context (±5 lines around comment range)

```
   558: def start_django(reloader, main_func, *args, **kwargs):
   559:     ensure_echo_on()
   560: 
   561:     main_func = check_errors(main_func)
   562:     django_main_thread = threading.Thread(target=main_func, args=args, kwargs=kwargs, name='django-main-thread')
>  563:     django_main_thread.setDaemon(True)
   564:     django_main_thread.start()
   565: 
   566:     while not reloader.should_stop:
   567:         try:
   568:             reloader.run(django_main_thread)
```

### Source context (±5 lines around oracle hunk)

```
   109: @functools.lru_cache(maxsize=1)
   110: def iter_modules_and_files(modules, extra_files):
   111:     """Iterate through all modules needed to be watched."""
   112:     sys_file_paths = []
   113:     for module in modules:
>  114:         # During debugging (with PyDev) the 'typing.io' and 'typing.re' objects
>  115:         # are added to sys.modules, however they are types not modules and so
>  116:         # cause issues here.
>  117:         if not isinstance(module, ModuleType) or getattr(module, '__spec__', None) is None:
>  118:             continue
>  119:         spec = module.__spec__
>  120:         # Modules could be loaded from places without a concrete location. If
   121:         # this is the case, skip them.
   122:         if spec.has_location:
   123:             origin = spec.loader.archive if isinstance(spec.loader, zipimporter) else spec.origin
   124:             sys_file_paths.append(origin)
   125: 
```

---

## Near-miss 4: claude-sonnet-4-5  /  django__django-11422

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `df46b329e0900e9e4dc1d60816c1dce6dfc1094e` |
| comment file (original) | `django/utils/autoreload.py` |
| comment file (normalised) | `django/utils/autoreload.py` |
| comment lines | 77-77 |
| nearest oracle site | `site-0001` |
| oracle file | `django/utils/autoreload.py` |
| oracle lines | 114-120 |
| distance (lines) | 37 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Exception constructor call may fail if the original exception requires arguments.

### Source context (±5 lines around comment range)

```
    72: 
    73: 
    74: def raise_last_exception():
    75:     global _exception
    76:     if _exception is not None:
>   77:         raise _exception[0](_exception[1]).with_traceback(_exception[2])
    78: 
    79: 
    80: def ensure_echo_on():
    81:     """
    82:     Ensure that echo mode is enabled. Some tools such as PDB disable
```

### Source context (±5 lines around oracle hunk)

```
   109: @functools.lru_cache(maxsize=1)
   110: def iter_modules_and_files(modules, extra_files):
   111:     """Iterate through all modules needed to be watched."""
   112:     sys_file_paths = []
   113:     for module in modules:
>  114:         # During debugging (with PyDev) the 'typing.io' and 'typing.re' objects
>  115:         # are added to sys.modules, however they are types not modules and so
>  116:         # cause issues here.
>  117:         if not isinstance(module, ModuleType) or getattr(module, '__spec__', None) is None:
>  118:             continue
>  119:         spec = module.__spec__
>  120:         # Modules could be loaded from places without a concrete location. If
   121:         # this is the case, skip them.
   122:         if spec.has_location:
   123:             origin = spec.loader.archive if isinstance(spec.loader, zipimporter) else spec.origin
   124:             sys_file_paths.append(origin)
   125: 
```

---

## Near-miss 5: claude-sonnet-4-5  /  django__django-12915

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `4652f1f0aa459a7b980441d629648707c32e36bf` |
| comment file (original) | `django/contrib/staticfiles/handlers.py` |
| comment file (normalised) | `django/contrib/staticfiles/handlers.py` |
| comment lines | 77-79 |
| nearest oracle site | `site-0002` |
| oracle file | `django/contrib/staticfiles/handlers.py` |
| oracle lines | 52-57 |
| distance (lines) | 20 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: ASGIStaticFilesHandler.__init__ does not call super().__init__(), unlike StaticFilesHandler which does.

### Source context (±5 lines around comment range)

```
    72: class ASGIStaticFilesHandler(StaticFilesHandlerMixin, ASGIHandler):
    73:     """
    74:     ASGI application which wraps another and intercepts requests for static
    75:     files, passing them off to Django's static file serving.
    76:     """
>   77:     def __init__(self, application):
>   78:         self.application = application
>   79:         self.base_url = urlparse(self.get_base_url())
    80: 
    81:     async def __call__(self, scope, receive, send):
    82:         # Only even look at HTTP requests
    83:         if scope['type'] == 'http' and self._should_handle(scope['path']):
    84:             # Serve static content
```

### Source context (±5 lines around oracle hunk)

```
    47:         return serve(request, self.file_path(request.path), insecure=True)
    48: 
    49:     def get_response(self, request):
    50:         try:
    51:             return self.serve(request)
>   52:         except Http404 as e:
>   53:             return response_for_exception(request, e)
>   54: 
>   55: 
>   56: class StaticFilesHandler(StaticFilesHandlerMixin, WSGIHandler):
>   57:     """
    58:     WSGI middleware that intercepts calls to the static files directory, as
    59:     defined by the STATIC_URL setting, and serves those files.
    60:     """
    61:     def __init__(self, application):
    62:         self.application = application
```

---

## Near-miss 6: claude-sonnet-4-5  /  django__django-13033

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e` |
| comment file (original) | `django/db/models/sql/compiler.py` |
| comment file (normalised) | `django/db/models/sql/compiler.py` |
| comment lines | 390-390 |
| nearest oracle site | `site-0001` |
| oracle file | `django/db/models/sql/compiler.py` |
| oracle lines | 727-733 |
| distance (lines) | 337 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Potential IndexError if regex search returns None or has no groups.

### Source context (±5 lines around comment range)

```
   385:             sql, params = self.compile(resolved)
   386:             # Don't add the same column twice, but the order direction is
   387:             # not taken into account so we strip it. When this entire method
   388:             # is refactored into expressions, then we can check each part as we
   389:             # generate it.
>  390:             without_ordering = self.ordering_parts.search(sql)[1]
   391:             params_hash = make_hashable(params)
   392:             if (without_ordering, params_hash) in seen:
   393:                 continue
   394:             seen.add((without_ordering, params_hash))
   395:             result.append((resolved, (sql, params, is_ref)))
```

### Source context (±5 lines around oracle hunk)

```
   722:         name, order = get_order_dir(name, default_order)
   723:         descending = order == 'DESC'
   724:         pieces = name.split(LOOKUP_SEP)
   725:         field, targets, alias, joins, path, opts, transform_function = self._setup_joins(pieces, opts, alias)
   726: 
>  727:         # If we get to this point and the field is a relation to another model,
>  728:         # append the default ordering for that model unless it is the pk
>  729:         # shortcut or the attribute name of the field that is specified.
>  730:         if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name and name != 'pk':
>  731:             # Firstly, avoid infinite loops.
>  732:             already_seen = already_seen or set()
>  733:             join_tuple = tuple(getattr(self.query.alias_map[j], 'join_cols', None) for j in joins)
   734:             if join_tuple in already_seen:
   735:                 raise FieldError('Infinite loop caused by ordering.')
   736:             already_seen.add(join_tuple)
   737: 
   738:             results = []
```

---

## Near-miss 7: claude-sonnet-4-5  /  django__django-13033

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e` |
| comment file (original) | `django/db/models/sql/compiler.py` |
| comment file (normalised) | `django/db/models/sql/compiler.py` |
| comment lines | 403-403 |
| nearest oracle site | `site-0001` |
| oracle file | `django/db/models/sql/compiler.py` |
| oracle lines | 727-733 |
| distance (lines) | 324 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Potential IndexError if regex search returns None or has no groups.

### Source context (±5 lines around comment range)

```
   398:     def get_extra_select(self, order_by, select):
   399:         extra_select = []
   400:         if self.query.distinct and not self.query.distinct_fields:
   401:             select_sql = [t[1] for t in select]
   402:             for expr, (sql, params, is_ref) in order_by:
>  403:                 without_ordering = self.ordering_parts.search(sql)[1]
   404:                 if not is_ref and (without_ordering, params) not in select_sql:
   405:                     extra_select.append((expr, (without_ordering, params), None))
   406:         return extra_select
   407: 
   408:     def quote_name_unless_alias(self, name):
```

### Source context (±5 lines around oracle hunk)

```
   722:         name, order = get_order_dir(name, default_order)
   723:         descending = order == 'DESC'
   724:         pieces = name.split(LOOKUP_SEP)
   725:         field, targets, alias, joins, path, opts, transform_function = self._setup_joins(pieces, opts, alias)
   726: 
>  727:         # If we get to this point and the field is a relation to another model,
>  728:         # append the default ordering for that model unless it is the pk
>  729:         # shortcut or the attribute name of the field that is specified.
>  730:         if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name and name != 'pk':
>  731:             # Firstly, avoid infinite loops.
>  732:             already_seen = already_seen or set()
>  733:             join_tuple = tuple(getattr(self.query.alias_map[j], 'join_cols', None) for j in joins)
   734:             if join_tuple in already_seen:
   735:                 raise FieldError('Infinite loop caused by ordering.')
   736:             already_seen.add(join_tuple)
   737: 
   738:             results = []
```

---

## Near-miss 8: claude-sonnet-4-5  /  django__django-13315

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `36bc47069ce071e80c8129500de3b8664d2058a7` |
| comment file (original) | `django/forms/models.py` |
| comment file (normalised) | `django/forms/models.py` |
| comment lines | 1357-1357 |
| nearest oracle site | `site-0001` |
| oracle file | `django/forms/models.py` |
| oracle lines | 97-106 |
| distance (lines) | 1251 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Filter result is created but never used, making the validation ineffective.

### Source context (±5 lines around comment range)

```
  1352:                 self.error_messages['invalid_list'],
  1353:                 code='invalid_list',
  1354:             )
  1355:         for pk in value:
  1356:             try:
> 1357:                 self.queryset.filter(**{key: pk})
  1358:             except (ValueError, TypeError):
  1359:                 raise ValidationError(
  1360:                     self.error_messages['invalid_pk_value'],
  1361:                     code='invalid_pk_value',
  1362:                     params={'pk': pk},
```

### Source context (±5 lines around oracle hunk)

```
    92:         if exclude and f.name in exclude:
    93:             continue
    94:         data[f.name] = f.value_from_object(instance)
    95:     return data
    96: 
>   97: 
>   98: def apply_limit_choices_to_to_formfield(formfield):
>   99:     """Apply limit_choices_to to the formfield's queryset if needed."""
>  100:     if hasattr(formfield, 'queryset') and hasattr(formfield, 'get_limit_choices_to'):
>  101:         limit_choices_to = formfield.get_limit_choices_to()
>  102:         if limit_choices_to is not None:
>  103:             formfield.queryset = formfield.queryset.complex_filter(limit_choices_to)
>  104: 
>  105: 
>  106: def fields_for_model(model, fields=None, exclude=None, widgets=None,
   107:                      formfield_callback=None, localized_fields=None,
   108:                      labels=None, help_texts=None, error_messages=None,
   109:                      field_classes=None, *, apply_limit_choices_to=True):
   110:     """
   111:     Return a dictionary containing form fields for the given model.
```

---

## Near-miss 9: claude-sonnet-4-5  /  django__django-13551

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `7f9e4524d6b23424cf44fbe1bf1f4e70f6bb066e` |
| comment file (original) | `django/contrib/auth/tokens.py` |
| comment file (normalised) | `django/contrib/auth/tokens.py` |
| comment lines | 104-104 |
| nearest oracle site | `site-0002` |
| oracle file | `django/contrib/auth/tokens.py` |
| oracle lines | 94-100 |
| distance (lines) | 4 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: datetime.now() returns naive datetime which may cause issues when comparing with timezone-aware last_login field.

### Source context (±5 lines around comment range)

```
    99:     def _num_seconds(self, dt):
   100:         return int((dt - datetime(2001, 1, 1)).total_seconds())
   101: 
   102:     def _now(self):
   103:         # Used for mocking in tests
>  104:         return datetime.now()
   105: 
   106: 
   107: default_token_generator = PasswordResetTokenGenerator()
```

### Source context (±5 lines around oracle hunk)

```
    89:         invalidates the token.
    90: 
    91:         Running this data through salted_hmac() prevents password cracking
    92:         attempts using the reset token, provided the secret isn't compromised.
    93:         """
>   94:         # Truncate microseconds so that tokens are consistent even if the
>   95:         # database doesn't support microseconds.
>   96:         login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
>   97:         return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)
>   98: 
>   99:     def _num_seconds(self, dt):
>  100:         return int((dt - datetime(2001, 1, 1)).total_seconds())
   101: 
   102:     def _now(self):
   103:         # Used for mocking in tests
   104:         return datetime.now()
   105: 
```

---

## Near-miss 10: claude-sonnet-4-5  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 1-1 |
| nearest oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| distance (lines) | 72 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: The 'cgi' module is deprecated since Python 3.11 and removed in Python 3.13.

### Source context (±5 lines around comment range)

```
>    1: import cgi
     2: import mimetypes
     3: import os
     4: import posixpath
     5: import shutil
     6: import stat
```

### Source context (±5 lines around oracle hunk)

```
    68:             top_dir = os.path.join(os.getcwd(), name)
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
    72:                 raise CommandError("'%s' already exists" % top_dir)
>   73:             except OSError as e:
>   74:                 raise CommandError(e)
>   75:         else:
>   76:             if app_or_project == 'app':
>   77:                 self.validate_name(os.path.basename(target), 'directory')
>   78:             top_dir = os.path.abspath(os.path.expanduser(target))
>   79:             if not os.path.exists(top_dir):
>   80:                 raise CommandError("Destination directory '%s' does not "
>   81:                                    "exist, please create it first." % top_dir)
    82: 
    83:         extensions = tuple(handle_extensions(options['extensions']))
    84:         extra_files = []
    85:         for file in options['files']:
    86:             extra_files.extend(map(lambda x: x.strip(), file.split(',')))
```

---

## Near-miss 11: claude-sonnet-4-5  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 270-270 |
| nearest oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| distance (lines) | 189 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: Using string split on path assumes Unix-style separators but should use os.path.basename.

### Source context (±5 lines around comment range)

```
   265:             the_path, info = urlretrieve(url, os.path.join(tempdir, filename))
   266:         except OSError as e:
   267:             raise CommandError("couldn't download URL %s to %s: %s" %
   268:                                (url, filename, e))
   269: 
>  270:         used_name = the_path.split('/')[-1]
   271: 
   272:         # Trying to get better name from response headers
   273:         content_disposition = info.get('content-disposition')
   274:         if content_disposition:
   275:             _, params = cgi.parse_header(content_disposition)
```

### Source context (±5 lines around oracle hunk)

```
    68:             top_dir = os.path.join(os.getcwd(), name)
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
    72:                 raise CommandError("'%s' already exists" % top_dir)
>   73:             except OSError as e:
>   74:                 raise CommandError(e)
>   75:         else:
>   76:             if app_or_project == 'app':
>   77:                 self.validate_name(os.path.basename(target), 'directory')
>   78:             top_dir = os.path.abspath(os.path.expanduser(target))
>   79:             if not os.path.exists(top_dir):
>   80:                 raise CommandError("Destination directory '%s' does not "
>   81:                                    "exist, please create it first." % top_dir)
    82: 
    83:         extensions = tuple(handle_extensions(options['extensions']))
    84:         extra_files = []
    85:         for file in options['files']:
    86:             extra_files.extend(map(lambda x: x.strip(), file.split(',')))
```

---

## Near-miss 12: claude-sonnet-4-5  /  django__django-16408

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `ef85b6bf0bc5a8b194f0724cf5bbedbcee402b96` |
| comment file (original) | `django/db/models/sql/compiler.py` |
| comment file (normalised) | `django/db/models/sql/compiler.py` |
| comment lines | 470-470 |
| nearest oracle site | `site-0001` |
| oracle file | `django/db/models/sql/compiler.py` |
| oracle lines | 1274-1279 |
| distance (lines) | 804 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Regex search result is accessed without checking if match exists, will raise AttributeError if no match found.

### Source context (±5 lines around comment range)

```
   465:             sql, params = self.compile(resolved)
   466:             # Don't add the same column twice, but the order direction is
   467:             # not taken into account so we strip it. When this entire method
   468:             # is refactored into expressions, then we can check each part as we
   469:             # generate it.
>  470:             without_ordering = self.ordering_parts.search(sql)[1]
   471:             params_hash = make_hashable(params)
   472:             if (without_ordering, params_hash) in seen:
   473:                 continue
   474:             seen.add((without_ordering, params_hash))
   475:             result.append((resolved, (sql, params, is_ref)))
```

### Source context (±5 lines around oracle hunk)

```
  1269:                 )
  1270:                 get_related_klass_infos(klass_info, next_klass_infos)
  1271: 
  1272:             def local_setter(final_field, obj, from_obj):
  1273:                 # Set a reverse fk object when relation is non-empty.
> 1274:                 if from_obj:
> 1275:                     final_field.remote_field.set_cached_value(from_obj, obj)
> 1276: 
> 1277:             def remote_setter(name, obj, from_obj):
> 1278:                 setattr(from_obj, name, obj)
> 1279: 
  1280:             for name in list(requested):
  1281:                 # Filtered relations work only on the topmost level.
  1282:                 if cur_depth > 1:
  1283:                     break
  1284:                 if name in self.query._filtered_relations:
```

---

## Near-miss 13: claude-sonnet-4-5  /  django__django-16408

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `ef85b6bf0bc5a8b194f0724cf5bbedbcee402b96` |
| comment file (original) | `django/db/models/sql/compiler.py` |
| comment file (normalised) | `django/db/models/sql/compiler.py` |
| comment lines | 483-483 |
| nearest oracle site | `site-0001` |
| oracle file | `django/db/models/sql/compiler.py` |
| oracle lines | 1274-1279 |
| distance (lines) | 791 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Regex search result is accessed without checking if match exists, will raise AttributeError if no match found.

### Source context (±5 lines around comment range)

```
   478:     def get_extra_select(self, order_by, select):
   479:         extra_select = []
   480:         if self.query.distinct and not self.query.distinct_fields:
   481:             select_sql = [t[1] for t in select]
   482:             for expr, (sql, params, is_ref) in order_by:
>  483:                 without_ordering = self.ordering_parts.search(sql)[1]
   484:                 if not is_ref and (without_ordering, params) not in select_sql:
   485:                     extra_select.append((expr, (without_ordering, params), None))
   486:         return extra_select
   487: 
   488:     def quote_name_unless_alias(self, name):
```

### Source context (±5 lines around oracle hunk)

```
  1269:                 )
  1270:                 get_related_klass_infos(klass_info, next_klass_infos)
  1271: 
  1272:             def local_setter(final_field, obj, from_obj):
  1273:                 # Set a reverse fk object when relation is non-empty.
> 1274:                 if from_obj:
> 1275:                     final_field.remote_field.set_cached_value(from_obj, obj)
> 1276: 
> 1277:             def remote_setter(name, obj, from_obj):
> 1278:                 setattr(from_obj, name, obj)
> 1279: 
  1280:             for name in list(requested):
  1281:                 # Filtered relations work only on the topmost level.
  1282:                 if cur_depth > 1:
  1283:                     break
  1284:                 if name in self.query._filtered_relations:
```

---

## Near-miss 14: claude-sonnet-4-5  /  django__django-16816

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `191f6a9a4586b5e5f79f4f42f190e7ad4bbacc84` |
| comment file (original) | `django/contrib/admin/checks.py` |
| comment file (normalised) | `django/contrib/admin/checks.py` |
| comment lines | 1000-1000 |
| nearest oracle site | `site-0001` |
| oracle file | `django/contrib/admin/checks.py` |
| oracle lines | 916-924 |
| distance (lines) | 76 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Using issubclass without _issubclass wrapper can raise TypeError if item is not a class.

### Source context (±5 lines around comment range)

```
   995:             if not _issubclass(item, ListFilter):
   996:                 return must_inherit_from(
   997:                     parent="ListFilter", option=label, obj=obj, id="admin.E113"
   998:                 )
   999:             # ...  but not a FieldListFilter.
> 1000:             elif issubclass(item, FieldListFilter):
  1001:                 return [
  1002:                     checks.Error(
  1003:                         "The value of '%s' must not inherit from 'FieldListFilter'."
  1004:                         % label,
  1005:                         obj=obj.__class__,
```

### Source context (±5 lines around oracle hunk)

```
   911:                             item,
   912:                             obj.__class__.__name__,
   913:                             obj.model._meta.label,
   914:                         ),
   915:                         obj=obj.__class__,
>  916:                         id="admin.E108",
>  917:                     )
>  918:                 ]
>  919:         if isinstance(field, models.ManyToManyField) or (
>  920:             getattr(field, "rel", None) and field.rel.field.many_to_one
>  921:         ):
>  922:             return [
>  923:                 checks.Error(
>  924:                     f"The value of '{label}' must not be a many-to-many field or a "
   925:                     f"reverse foreign key.",
   926:                     obj=obj.__class__,
   927:                     id="admin.E109",
   928:                 )
   929:             ]
```

---

## Near-miss 15: claude-sonnet-4-5  /  django__django-17087

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `4a72da71001f154ea60906a2f74898d32b7322a7` |
| comment file (original) | `django/db/migrations/serializer.py` |
| comment file (normalised) | `django/db/migrations/serializer.py` |
| comment lines | 291-291 |
| nearest oracle site | `site-0001` |
| oracle file | `django/db/migrations/serializer.py` |
| oracle lines | 168-174 |
| distance (lines) | 117 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Empty set serialization produces 'set()' but _format returns string with '%s' placeholder that expects content, resulting in 'set([])' instead of 'set()'.

### Source context (±5 lines around comment range)

```
   286: 
   287: class SetSerializer(BaseUnorderedSequenceSerializer):
   288:     def _format(self):
   289:         # Serialize as a set literal except when value is empty because {}
   290:         # is an empty dict.
>  291:         return "{%s}" if self.value else "set(%s)"
   292: 
   293: 
   294: class SettingsReferenceSerializer(BaseSerializer):
   295:     def serialize(self):
   296:         return "settings.%s" % self.value.setting_name, {
```

### Source context (±5 lines around oracle hunk)

```
   163: 
   164: class FunctionTypeSerializer(BaseSerializer):
   165:     def serialize(self):
   166:         if getattr(self.value, "__self__", None) and isinstance(
   167:             self.value.__self__, type
>  168:         ):
>  169:             klass = self.value.__self__
>  170:             module = klass.__module__
>  171:             return "%s.%s.%s" % (module, klass.__name__, self.value.__name__), {
>  172:                 "import %s" % module
>  173:             }
>  174:         # Further error checking
   175:         if self.value.__name__ == "<lambda>":
   176:             raise ValueError("Cannot serialize function: lambda")
   177:         if self.value.__module__ is None:
   178:             raise ValueError("Cannot serialize function %r: No module" % self.value)
   179: 
```

---

## Near-miss 16: claude-sonnet-4-5  /  matplotlib__matplotlib-23476

| field | value |
|---|---|
| repo | `matplotlib/matplotlib` |
| base_commit | `33a0599711d26dc2b79f851c6daed4947df7c167` |
| comment file (original) | `lib/matplotlib/figure.py` |
| comment file (normalised) | `lib/matplotlib/figure.py` |
| comment lines | 2383-2383 |
| nearest oracle site | `site-0001` |
| oracle file | `lib/matplotlib/figure.py` |
| oracle lines | 3023-3028 |
| distance (lines) | 640 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: Duplicate connection of 'key_release_event' handler at line 2383 (already connected at line 2382).

### Source context (±5 lines around comment range)

```
  2378:             'scroll_event', self.pick)
  2379:         connect = self._canvas_callbacks._connect_picklable
  2380:         self._mouse_key_ids = [
  2381:             connect('key_press_event', backend_bases._key_handler),
  2382:             connect('key_release_event', backend_bases._key_handler),
> 2383:             connect('key_release_event', backend_bases._key_handler),
  2384:             connect('button_press_event', backend_bases._mouse_handler),
  2385:             connect('button_release_event', backend_bases._mouse_handler),
  2386:             connect('scroll_event', backend_bases._mouse_handler),
  2387:             connect('motion_notify_event', backend_bases._mouse_handler),
  2388:         ]
```

### Source context (±5 lines around oracle hunk)

```
  3018:         # The canvas cannot currently be pickled, but this has the benefit
  3019:         # of meaning that a figure can be detached from one canvas, and
  3020:         # re-attached to another.
  3021:         state.pop("canvas")
  3022: 
> 3023:         # Set cached renderer to None -- it can't be pickled.
> 3024:         state["_cachedRenderer"] = None
> 3025: 
> 3026:         # add version information to the state
> 3027:         state['__mpl_version__'] = mpl.__version__
> 3028: 
  3029:         # check whether the figure manager (if any) is registered with pyplot
  3030:         from matplotlib import _pylab_helpers
  3031:         if self.canvas.manager in _pylab_helpers.Gcf.figs.values():
  3032:             state['_restore_to_pylab'] = True
  3033:         return state
```

---

## Near-miss 17: claude-sonnet-4-5  /  matplotlib__matplotlib-23476

| field | value |
|---|---|
| repo | `matplotlib/matplotlib` |
| base_commit | `33a0599711d26dc2b79f851c6daed4947df7c167` |
| comment file (original) | `lib/matplotlib/figure.py` |
| comment file (normalised) | `lib/matplotlib/figure.py` |
| comment lines | 404-405 |
| nearest oracle site | `site-0001` |
| oracle file | `lib/matplotlib/figure.py` |
| oracle lines | 3023-3028 |
| distance (lines) | 2618 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: Dictionary key 'rotation_mode' is added to info dict but not used in _suplabels method.

### Source context (±5 lines around comment range)

```
   399:                              va='center')
   400:     @_docstring.copy(_suplabels)
   401:     def supylabel(self, t, **kwargs):
   402:         # docstring from _suplabels...
   403:         info = {'name': '_supylabel', 'x0': 0.02, 'y0': 0.5,
>  404:                 'ha': 'left', 'va': 'center', 'rotation': 'vertical',
>  405:                 'rotation_mode': 'anchor'}
   406:         return self._suplabels(t, info, **kwargs)
   407: 
   408:     def get_edgecolor(self):
   409:         """Get the edge color of the Figure rectangle."""
   410:         return self.patch.get_edgecolor()
```

### Source context (±5 lines around oracle hunk)

```
  3018:         # The canvas cannot currently be pickled, but this has the benefit
  3019:         # of meaning that a figure can be detached from one canvas, and
  3020:         # re-attached to another.
  3021:         state.pop("canvas")
  3022: 
> 3023:         # Set cached renderer to None -- it can't be pickled.
> 3024:         state["_cachedRenderer"] = None
> 3025: 
> 3026:         # add version information to the state
> 3027:         state['__mpl_version__'] = mpl.__version__
> 3028: 
  3029:         # check whether the figure manager (if any) is registered with pyplot
  3030:         from matplotlib import _pylab_helpers
  3031:         if self.canvas.manager in _pylab_helpers.Gcf.figs.values():
  3032:             state['_restore_to_pylab'] = True
  3033:         return state
```

---

## Near-miss 18: claude-sonnet-4-5  /  sphinx-doc__sphinx-8282

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `2c2335bbb8af99fa132e1573bbf45dc91584d5a2` |
| comment file (original) | `sphinx/ext/autodoc/__init__.py` |
| comment file (normalised) | `sphinx/ext/autodoc/__init__.py` |
| comment lines | 1932-1933 |
| nearest oracle site | `site-0003` |
| oracle file | `sphinx/ext/autodoc/__init__.py` |
| oracle lines | 1882-1888 |
| distance (lines) | 44 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Off-by-one error: checks `len(sig.parameters) == 1` but accesses `params[1]`, which would cause IndexError.

### Source context (±5 lines around comment range)

```
  1927:             logger.warning(__("Failed to get a method signature for %s: %s"),
  1928:                            self.fullname, exc)
  1929:             return
  1930:         except ValueError:
  1931:             return
> 1932:         if len(sig.parameters) == 1:
> 1933:             return
  1934: 
  1935:         params = list(sig.parameters.values())
  1936:         if params[1].annotation is Parameter.empty:
  1937:             params[1] = params[1].replace(annotation=typ)
  1938:             try:
```

### Source context (±5 lines around oracle hunk)

```
  1877:         if self.analyzer and '.'.join(self.objpath) in self.analyzer.finals:
  1878:             self.add_line('   :final:', sourcename)
  1879: 
  1880:     def document_members(self, all_members: bool = False) -> None:
  1881:         pass
> 1882: 
> 1883:     def format_signature(self, **kwargs: Any) -> str:
> 1884:         sigs = []
> 1885:         if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
> 1886:             # Use signatures for overloaded methods instead of the implementation method.
> 1887:             overloaded = True
> 1888:         else:
  1889:             overloaded = False
  1890:             sig = super().format_signature(**kwargs)
  1891:             sigs.append(sig)
  1892: 
  1893:         meth = self.parent.__dict__.get(self.objpath[-1])
```

---

## Near-miss 19: claude-sonnet-4-5  /  sphinx-doc__sphinx-8282

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `2c2335bbb8af99fa132e1573bbf45dc91584d5a2` |
| comment file (original) | `sphinx/ext/autodoc/__init__.py` |
| comment file (normalised) | `sphinx/ext/autodoc/__init__.py` |
| comment lines | 1285-1286 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/ext/autodoc/__init__.py` |
| oracle lines | 1240-1246 |
| distance (lines) | 39 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: Inconsistent early return check: returns early if `len(sig.parameters) == 0` but similar function at line 1932 checks for `== 1`.

### Source context (±5 lines around comment range)

```
  1280:                            self.fullname, exc)
  1281:             return
  1282:         except ValueError:
  1283:             return
  1284: 
> 1285:         if len(sig.parameters) == 0:
> 1286:             return
  1287: 
  1288:         params = list(sig.parameters.values())
  1289:         if params[0].annotation is Parameter.empty:
  1290:             params[0] = params[0].replace(annotation=typ)
  1291:             try:
```

### Source context (±5 lines around oracle hunk)

```
  1235:         sourcename = self.get_sourcename()
  1236:         super().add_directive_header(sig)
  1237: 
  1238:         if inspect.iscoroutinefunction(self.object):
  1239:             self.add_line('   :async:', sourcename)
> 1240: 
> 1241:     def format_signature(self, **kwargs: Any) -> str:
> 1242:         sigs = []
> 1243:         if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
> 1244:             # Use signatures for overloaded functions instead of the implementation function.
> 1245:             overloaded = True
> 1246:         else:
  1247:             overloaded = False
  1248:             sig = super().format_signature(**kwargs)
  1249:             sigs.append(sig)
  1250: 
  1251:         if inspect.is_singledispatch_function(self.object):
```

---

## Near-miss 20: claude-sonnet-4-5  /  sphinx-doc__sphinx-8474

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `3ea1ec84cc610f7a9f4f6b354e264565254923ff` |
| comment file (original) | `sphinx/domains/std.py` |
| comment file (normalised) | `sphinx/domains/std.py` |
| comment lines | 236-236 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/domains/std.py` |
| oracle lines | 852-859 |
| distance (lines) | 616 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Using first ID from signode['ids'] list which may be empty or contain wrong ID after multiple IDs were appended in lines 224-229.

### Source context (±5 lines around comment range)

```
   231:         self.state.document.note_explicit_target(signode)
   232: 
   233:         domain = cast(StandardDomain, self.env.get_domain('std'))
   234:         for optname in signode.get('allnames', []):
   235:             domain.add_program_option(currprogram, optname,
>  236:                                       self.env.docname, signode['ids'][0])
   237: 
   238:         # create an index entry
   239:         if currprogram:
   240:             descr = _('%s command line option') % currprogram
   241:         else:
```

### Source context (±5 lines around oracle hunk)

```
   847:             logger.warning(__('numfig is disabled. :numref: is ignored.'), location=node)
   848:             return contnode
   849: 
   850:         try:
   851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>  852:             if fignumber is None:
>  853:                 return contnode
>  854:         except ValueError:
>  855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>  856:                            location=node)
>  857:             return contnode
>  858: 
>  859:         try:
   860:             if node['refexplicit']:
   861:                 title = contnode.astext()
   862:             else:
   863:                 title = env.config.numfig_format.get(figtype, '')
   864: 
```

---

## Near-miss 21: claude-sonnet-4-5  /  sphinx-doc__sphinx-8474

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `3ea1ec84cc610f7a9f4f6b354e264565254923ff` |
| comment file (original) | `sphinx/domains/std.py` |
| comment file (normalised) | `sphinx/domains/std.py` |
| comment lines | 245-245 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/domains/std.py` |
| oracle lines | 852-859 |
| distance (lines) | 607 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Using first ID from signode['ids'] list which may be empty or contain wrong ID after multiple IDs were appended in lines 224-229.

### Source context (±5 lines around comment range)

```
   240:             descr = _('%s command line option') % currprogram
   241:         else:
   242:             descr = _('command line option')
   243:         for option in sig.split(', '):
   244:             entry = '; '.join([descr, option])
>  245:             self.indexnode['entries'].append(('pair', entry, signode['ids'][0], '', None))
   246: 
   247:     def make_old_id(self, prefix: str, optname: str) -> str:
   248:         """Generate old styled node_id for cmdoption.
   249: 
   250:         .. note:: Old Styled node_id was used until Sphinx-3.0.
```

### Source context (±5 lines around oracle hunk)

```
   847:             logger.warning(__('numfig is disabled. :numref: is ignored.'), location=node)
   848:             return contnode
   849: 
   850:         try:
   851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>  852:             if fignumber is None:
>  853:                 return contnode
>  854:         except ValueError:
>  855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>  856:                            location=node)
>  857:             return contnode
>  858: 
>  859:         try:
   860:             if node['refexplicit']:
   861:                 title = contnode.astext()
   862:             else:
   863:                 title = env.config.numfig_format.get(figtype, '')
   864: 
```

---

## Near-miss 22: claude-sonnet-4-5  /  sphinx-doc__sphinx-8474

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `3ea1ec84cc610f7a9f4f6b354e264565254923ff` |
| comment file (original) | `sphinx/domains/std.py` |
| comment file (normalised) | `sphinx/domains/std.py` |
| comment lines | 541-541 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/domains/std.py` |
| oracle lines | 852-859 |
| distance (lines) | 311 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Checking title[0] without verifying title is non-empty could raise IndexError.

### Source context (±5 lines around comment range)

```
   536: 
   537: class TokenXRefRole(XRefRole):
   538:     def process_link(self, env: "BuildEnvironment", refnode: Element, has_explicit_title: bool,
   539:                      title: str, target: str) -> Tuple[str, str]:
   540:         target = target.lstrip('~')  # a title-specific thing
>  541:         if not self.has_explicit_title and title[0] == '~':
   542:             if ':' in title:
   543:                 _, title = title.split(':')
   544:             else:
   545:                 title = title[1:]
   546:         return title, target
```

### Source context (±5 lines around oracle hunk)

```
   847:             logger.warning(__('numfig is disabled. :numref: is ignored.'), location=node)
   848:             return contnode
   849: 
   850:         try:
   851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>  852:             if fignumber is None:
>  853:                 return contnode
>  854:         except ValueError:
>  855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>  856:                            location=node)
>  857:             return contnode
>  858: 
>  859:         try:
   860:             if node['refexplicit']:
   861:                 title = contnode.astext()
   862:             else:
   863:                 title = env.config.numfig_format.get(figtype, '')
   864: 
```

---

## Near-miss 23: claude-sonnet-4-5  /  sphinx-doc__sphinx-8474

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `3ea1ec84cc610f7a9f4f6b354e264565254923ff` |
| comment file (original) | `sphinx/domains/std.py` |
| comment file (normalised) | `sphinx/domains/std.py` |
| comment lines | 667-668 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/domains/std.py` |
| oracle lines | 852-859 |
| distance (lines) | 184 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Tuple unpacking assumes objects dictionary values are 2-tuples, but could fail if data is corrupted.

### Source context (±5 lines around comment range)

```
   662:                     ) -> None:
   663:         """Note a generic object for cross reference.
   664: 
   665:         .. versionadded:: 3.0
   666:         """
>  667:         if (objtype, name) in self.objects:
>  668:             docname = self.objects[objtype, name][0]
   669:             logger.warning(__('duplicate %s description of %s, other instance in %s'),
   670:                            objtype, name, docname, location=location)
   671:         self.objects[objtype, name] = (self.env.docname, labelid)
   672: 
   673:     def add_object(self, objtype: str, name: str, docname: str, labelid: str) -> None:
```

### Source context (±5 lines around oracle hunk)

```
   847:             logger.warning(__('numfig is disabled. :numref: is ignored.'), location=node)
   848:             return contnode
   849: 
   850:         try:
   851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>  852:             if fignumber is None:
>  853:                 return contnode
>  854:         except ValueError:
>  855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>  856:                            location=node)
>  857:             return contnode
>  858: 
>  859:         try:
   860:             if node['refexplicit']:
   861:                 title = contnode.astext()
   862:             else:
   863:                 title = env.config.numfig_format.get(figtype, '')
   864: 
```

---

## Near-miss 24: claude-sonnet-4-5  /  sphinx-doc__sphinx-8474

| field | value |
|---|---|
| repo | `sphinx-doc/sphinx` |
| base_commit | `3ea1ec84cc610f7a9f4f6b354e264565254923ff` |
| comment file (original) | `sphinx/domains/std.py` |
| comment file (normalised) | `sphinx/domains/std.py` |
| comment lines | 870-870 |
| nearest oracle site | `site-0001` |
| oracle file | `sphinx/domains/std.py` |
| oracle lines | 852-859 |
| distance (lines) | 11 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: String 'number' checked with 'in' operator but should be '{number}' to match format string pattern.

### Source context (±5 lines around comment range)

```
   865:             if figname is None and '{name}' in title:
   866:                 logger.warning(__('the link has no caption: %s'), title, location=node)
   867:                 return contnode
   868:             else:
   869:                 fignum = '.'.join(map(str, fignumber))
>  870:                 if '{name}' in title or 'number' in title:
   871:                     # new style format (cf. "Fig.{number}")
   872:                     if figname:
   873:                         newtitle = title.format(name=figname, number=fignum)
   874:                     else:
   875:                         newtitle = title.format(number=fignum)
```

### Source context (±5 lines around oracle hunk)

```
   847:             logger.warning(__('numfig is disabled. :numref: is ignored.'), location=node)
   848:             return contnode
   849: 
   850:         try:
   851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>  852:             if fignumber is None:
>  853:                 return contnode
>  854:         except ValueError:
>  855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>  856:                            location=node)
>  857:             return contnode
>  858: 
>  859:         try:
   860:             if node['refexplicit']:
   861:                 title = contnode.astext()
   862:             else:
   863:                 title = env.config.numfig_format.get(figtype, '')
   864: 
```

---

## Near-miss 25: claude-sonnet-4-5  /  sympy__sympy-16792

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `09786a173e7a0a488f46dd6000177c23e5d24eed` |
| comment file (original) | `sympy/utilities/codegen.py` |
| comment file (normalised) | `sympy/utilities/codegen.py` |
| comment lines | 277-277 |
| nearest oracle site | `site-0001` |
| oracle file | `sympy/utilities/codegen.py` |
| oracle lines | 695-700 |
| distance (lines) | 418 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Identity comparison 'is' used instead of equality '==' for string comparison.

### Source context (±5 lines around comment range)

```
   272:         return default_datatypes["float"]
   273:     elif isinstance(expr, MatrixBase):
   274:         #check all entries
   275:         dt = "int"
   276:         for element in expr:
>  277:             if dt is "int" and not element.is_integer:
   278:                 dt = "float"
   279:             if dt is "float" and not element.is_real:
   280:                 return default_datatypes[final_dtype]
   281:         return default_datatypes[dt]
   282:     else:
```

### Source context (±5 lines around oracle hunk)

```
   690:                 output_args.append(
   691:                     OutputArgument(out_arg, out_arg, expr, dimensions=dims))
   692:             else:
   693:                 return_val.append(Result(expr))
   694: 
>  695:         arg_list = []
>  696: 
>  697:         # setup input argument list
>  698:         array_symbols = {}
>  699:         for array in expressions.atoms(Indexed) | local_expressions.atoms(Indexed):
>  700:             array_symbols[array.base.label] = array
   701:         for array in expressions.atoms(MatrixSymbol) | local_expressions.atoms(MatrixSymbol):
   702:             array_symbols[array] = array
   703: 
   704:         for symbol in sorted(symbols, key=str):
   705:             if symbol in array_symbols:
```

---

## Near-miss 26: claude-sonnet-4-5  /  sympy__sympy-16792

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `09786a173e7a0a488f46dd6000177c23e5d24eed` |
| comment file (original) | `sympy/utilities/codegen.py` |
| comment file (normalised) | `sympy/utilities/codegen.py` |
| comment lines | 279-279 |
| nearest oracle site | `site-0001` |
| oracle file | `sympy/utilities/codegen.py` |
| oracle lines | 695-700 |
| distance (lines) | 416 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Identity comparison 'is' used instead of equality '==' for string comparison.

### Source context (±5 lines around comment range)

```
   274:         #check all entries
   275:         dt = "int"
   276:         for element in expr:
   277:             if dt is "int" and not element.is_integer:
   278:                 dt = "float"
>  279:             if dt is "float" and not element.is_real:
   280:                 return default_datatypes[final_dtype]
   281:         return default_datatypes[dt]
   282:     else:
   283:         return default_datatypes[final_dtype]
   284: 
```

### Source context (±5 lines around oracle hunk)

```
   690:                 output_args.append(
   691:                     OutputArgument(out_arg, out_arg, expr, dimensions=dims))
   692:             else:
   693:                 return_val.append(Result(expr))
   694: 
>  695:         arg_list = []
>  696: 
>  697:         # setup input argument list
>  698:         array_symbols = {}
>  699:         for array in expressions.atoms(Indexed) | local_expressions.atoms(Indexed):
>  700:             array_symbols[array.base.label] = array
   701:         for array in expressions.atoms(MatrixSymbol) | local_expressions.atoms(MatrixSymbol):
   702:             array_symbols[array] = array
   703: 
   704:         for symbol in sorted(symbols, key=str):
   705:             if symbol in array_symbols:
```

---

## Near-miss 27: claude-sonnet-4-5  /  sympy__sympy-16792

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `09786a173e7a0a488f46dd6000177c23e5d24eed` |
| comment file (original) | `sympy/utilities/codegen.py` |
| comment file (normalised) | `sympy/utilities/codegen.py` |
| comment lines | 958-958 |
| nearest oracle site | `site-0003` |
| oracle file | `sympy/utilities/codegen.py` |
| oracle lines | 739-745 |
| distance (lines) | 213 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: CodeGen is called as a function but it's a class, should be CodeGenError.

### Source context (±5 lines around comment range)

```
   953:             # for loops are defined declared elsewhere.
   954:             if not isinstance(result, Result):
   955:                 continue
   956: 
   957:             if result.name != result.result_var:
>  958:                 raise CodeGen("Result variable and name should match: {}".format(result))
   959:             assign_to = result.name
   960:             t = result.get_datatype('c')
   961:             if isinstance(result.expr, (MatrixBase, MatrixExpr)):
   962:                 dims = result.expr.shape
   963:                 if dims[1] != 1:
```

### Source context (±5 lines around oracle hunk)

```
   734: 
   735:             # create redundant arguments to produce the requested sequence
   736:             name_arg_dict = {x.name: x for x in arg_list}
   737:             new_args = []
   738:             for symbol in argument_sequence:
>  739:                 try:
>  740:                     new_args.append(name_arg_dict[symbol])
>  741:                 except KeyError:
>  742:                     new_args.append(InputArgument(symbol))
>  743:             arg_list = new_args
>  744: 
>  745:         return Routine(name, arg_list, return_val, local_vars, global_vars)
   746: 
   747:     def write(self, routines, prefix, to_files=False, header=True, empty=True):
   748:         """Writes all the source code files for the given routines.
   749: 
   750:         The generated source is returned as a list of (filename, contents)
```

---

## Near-miss 28: claude-sonnet-4-5  /  sympy__sympy-16792

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `09786a173e7a0a488f46dd6000177c23e5d24eed` |
| comment file (original) | `sympy/utilities/codegen.py` |
| comment file (normalised) | `sympy/utilities/codegen.py` |
| comment lines | 964-964 |
| nearest oracle site | `site-0003` |
| oracle file | `sympy/utilities/codegen.py` |
| oracle lines | 739-745 |
| distance (lines) | 219 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | low |

**Message**: Typo in error message: 'variabels' should be 'variables'.

### Source context (±5 lines around comment range)

```
   959:             assign_to = result.name
   960:             t = result.get_datatype('c')
   961:             if isinstance(result.expr, (MatrixBase, MatrixExpr)):
   962:                 dims = result.expr.shape
   963:                 if dims[1] != 1:
>  964:                     raise CodeGenError("Only column vectors are supported in local variabels. Local result {} has dimensions {}".format(result, dims))
   965:                 code_lines.append("{0} {1}[{2}];\n".format(t, str(assign_to), dims[0]))
   966:                 prefix = ""
   967:             else:
   968:                 prefix = "const {0} ".format(t)
   969: 
```

### Source context (±5 lines around oracle hunk)

```
   734: 
   735:             # create redundant arguments to produce the requested sequence
   736:             name_arg_dict = {x.name: x for x in arg_list}
   737:             new_args = []
   738:             for symbol in argument_sequence:
>  739:                 try:
>  740:                     new_args.append(name_arg_dict[symbol])
>  741:                 except KeyError:
>  742:                     new_args.append(InputArgument(symbol))
>  743:             arg_list = new_args
>  744: 
>  745:         return Routine(name, arg_list, return_val, local_vars, global_vars)
   746: 
   747:     def write(self, routines, prefix, to_files=False, header=True, empty=True):
   748:         """Writes all the source code files for the given routines.
   749: 
   750:         The generated source is returned as a list of (filename, contents)
```

---

## Near-miss 29: claude-sonnet-4-5  /  sympy__sympy-20442

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `1abbc0ac3e552cb184317194e5d5c5b9dd8fb640` |
| comment file (original) | `sympy/physics/units/util.py` |
| comment file (normalised) | `sympy/physics/units/util.py` |
| comment lines | 134-134 |
| nearest oracle site | `site-0002` |
| oracle file | `sympy/physics/units/util.py` |
| oracle lines | 30-36 |
| distance (lines) | 98 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | high |

**Message**: Dictionary comprehension iterates over the same set it's building from, causing undefined behavior.

### Source context (±5 lines around comment range)

```
   129:     if expr.is_Atom or not expr.has(Prefix, Quantity):
   130:         return expr
   131: 
   132:     # replace all prefixes with numerical values
   133:     p = expr.atoms(Prefix)
>  134:     expr = expr.xreplace({p: p.scale_factor for p in p})
   135: 
   136:     # replace all quantities of given dimension with a canonical
   137:     # quantity, chosen from those in the expression
   138:     d = sift(expr.atoms(Quantity), lambda i: i.dimension)
   139:     for k in d:
```

### Source context (±5 lines around oracle hunk)

```
    25:         return None
    26: 
    27:     seen = set()
    28:     canon_dim_units = [i for i in canon_dim_units if not (i in seen or seen.add(i))]
    29: 
>   30:     camat = Matrix([[dimension_system.get_dimensional_dependencies(i, mark_dimensionless=True).get(j, 0) for i in target_dims] for j in canon_dim_units])
>   31:     exprmat = Matrix([dim_dependencies.get(k, 0) for k in canon_dim_units])
>   32: 
>   33:     res_exponents = camat.solve_least_squares(exprmat, method=None)
>   34:     return res_exponents
>   35: 
>   36: 
    37: def convert_to(expr, target_units, unit_system="SI"):
    38:     """
    39:     Convert ``expr`` to the same expression with all of its units and quantities
    40:     represented as factors of ``target_units``, whenever the dimension is compatible.
    41: 
```

---

## Near-miss 30: claude-sonnet-4-5  /  sympy__sympy-21627

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `126f80578140e752ad5135aac77b8ff887eede3e` |
| comment file (original) | `sympy/functions/elementary/complexes.py` |
| comment file (normalised) | `sympy/functions/elementary/complexes.py` |
| comment lines | 1232-1232 |
| nearest oracle site | `site-0001` |
| oracle file | `sympy/functions/elementary/complexes.py` |
| oracle lines | 607-612 |
| distance (lines) | 620 |
| tolerance (Round 1) | 3 |
| is_hit in results.csv | False |
| severity | medium |

**Message**: Method 'eval' is a classmethod but uses 'self' instead of 'cls' as first parameter.

### Source context (±5 lines around comment range)

```
  1227: 
  1228:     is_polar = True
  1229:     is_comparable = False  # cannot always be evalf'd
  1230: 
  1231:     @classmethod
> 1232:     def eval(self, x, period):
  1233:         from sympy import oo, exp_polar, I, Mul, polar_lift, Symbol
  1234:         if isinstance(x, polar_lift):
  1235:             return principal_branch(x.args[0], period)
  1236:         if period == oo:
  1237:             return x
```

### Source context (±5 lines around oracle hunk)

```
   602:         if arg.is_extended_nonnegative:
   603:             return arg
   604:         if arg.is_extended_nonpositive:
   605:             return -arg
   606:         if arg.is_imaginary:
>  607:             arg2 = -S.ImaginaryUnit * arg
>  608:             if arg2.is_extended_nonnegative:
>  609:                 return arg2
>  610:         # reject result if all new conjugates are just wrappers around
>  611:         # an expression that was already in the arg
>  612:         conj = signsimp(arg.conjugate(), evaluate=False)
   613:         new_conj = conj.atoms(conjugate) - arg.atoms(conjugate)
   614:         if new_conj and all(arg.has(i.args[0]) for i in new_conj):
   615:             return
   616:         if arg != conj and arg != -conj:
   617:             ignore = arg.atoms(Abs)
```

---

