# E.3 Oracle sanity check (3 random instances)

Sampled from the 20 Round 1 instance IDs with ``random.Random(42).sample(all_20_ids, 3)``. Selected IDs: ['django__django-11422', 'django__django-11099', 'django__django-14382']

# Instance 1: `django__django-11422`

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `df46b329e0900e9e4dc1d60816c1dce6dfc1094e` |
| patch length (chars) | 1097 |

## Raw fix-patch hunks

_Note: raw patch text is in this diagnostic file only; reviewers never see it._

#### File: `a/django/utils/autoreload.py` -> `b/django/utils/autoreload.py` (1 hunks)

```diff
@@ -114,7 +114,15 @@ def iter_modules_and_files(modules, extra_files):
         # During debugging (with PyDev) the 'typing.io' and 'typing.re' objects
         # are added to sys.modules, however they are types not modules and so
         # cause issues here.
-        if not isinstance(module, ModuleType) or getattr(module, '__spec__', None) is None:
+        if not isinstance(module, ModuleType):
+            continue
+        if module.__name__ == '__main__':
+            # __main__ (usually manage.py) doesn't always have a __spec__ set.
+            # Handle this by falling back to using __file__, resolved below.
+            # See https://docs.python.org/reference/import.html#main-spec
+            sys_file_paths.append(module.__file__)
+            continue
+        if getattr(module, '__spec__', None) is None:
             continue
         spec = module.__spec__
         # Modules could be loaded from places without a concrete location. If
```

## Parsed oracle sites (strict_mode=False, Round 1 setting)

| site_id | file | lines |
|---|---|---|
| site-0001 | django/utils/autoreload.py | 114-120 |

## Source context ±5 lines around each oracle hunk

### site-0001 `django/utils/autoreload.py` lines 114-120

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

# Instance 2: `django__django-11099`

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `d26b2424437dabeeca94d7900b37d2df4410da0c` |
| patch length (chars) | 808 |

## Raw fix-patch hunks

_Note: raw patch text is in this diagnostic file only; reviewers never see it._

#### File: `a/django/contrib/auth/validators.py` -> `b/django/contrib/auth/validators.py` (2 hunks)

```diff
@@ -7,7 +7,7 @@
 
 @deconstructible
 class ASCIIUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
     message = _(
         'Enter a valid username. This value may contain only English letters, '
         'numbers, and @/./+/-/_ characters.'
```

```diff
@@ -17,7 +17,7 @@ class ASCIIUsernameValidator(validators.RegexValidator):
 
 @deconstructible
 class UnicodeUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
     message = _(
         'Enter a valid username. This value may contain only letters, '
         'numbers, and @/./+/-/_ characters.'
```

## Parsed oracle sites (strict_mode=False, Round 1 setting)

| site_id | file | lines |
|---|---|---|
| site-0001 | django/contrib/auth/validators.py | 7-13 |
| site-0002 | django/contrib/auth/validators.py | 17-23 |

## Source context ±5 lines around each oracle hunk

### site-0001 `django/contrib/auth/validators.py` lines 7-13

```
     2: 
     3: from django.core import validators
     4: from django.utils.deconstruct import deconstructible
     5: from django.utils.translation import gettext_lazy as _
     6: 
>    7: 
>    8: @deconstructible
>    9: class ASCIIUsernameValidator(validators.RegexValidator):
>   10:     regex = r'^[\w.@+-]+$'
>   11:     message = _(
>   12:         'Enter a valid username. This value may contain only English letters, '
>   13:         'numbers, and @/./+/-/_ characters.'
    14:     )
    15:     flags = re.ASCII
    16: 
    17: 
    18: @deconstructible
```

### site-0002 `django/contrib/auth/validators.py` lines 17-23

```
    12:         'Enter a valid username. This value may contain only English letters, '
    13:         'numbers, and @/./+/-/_ characters.'
    14:     )
    15:     flags = re.ASCII
    16: 
>   17: 
>   18: @deconstructible
>   19: class UnicodeUsernameValidator(validators.RegexValidator):
>   20:     regex = r'^[\w.@+-]+$'
>   21:     message = _(
>   22:         'Enter a valid username. This value may contain only letters, '
>   23:         'numbers, and @/./+/-/_ characters.'
    24:     )
    25:     flags = 0
```

---

# Instance 3: `django__django-14382`

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| patch length (chars) | 841 |

## Raw fix-patch hunks

_Note: raw patch text is in this diagnostic file only; reviewers never see it._

#### File: `a/django/core/management/templates.py` -> `b/django/core/management/templates.py` (1 hunks)

```diff
@@ -73,9 +73,9 @@ def handle(self, app_or_project, name, target=None, **options):
             except OSError as e:
                 raise CommandError(e)
         else:
-            if app_or_project == 'app':
-                self.validate_name(os.path.basename(target), 'directory')
             top_dir = os.path.abspath(os.path.expanduser(target))
+            if app_or_project == 'app':
+                self.validate_name(os.path.basename(top_dir), 'directory')
             if not os.path.exists(top_dir):
                 raise CommandError("Destination directory '%s' does not "
                                    "exist, please create it first." % top_dir)
```

## Parsed oracle sites (strict_mode=False, Round 1 setting)

| site_id | file | lines |
|---|---|---|
| site-0001 | django/core/management/templates.py | 73-81 |

## Source context ±5 lines around each oracle hunk

### site-0001 `django/core/management/templates.py` lines 73-81

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

