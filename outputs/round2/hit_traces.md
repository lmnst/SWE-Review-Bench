# E.2 Round 1 hit traces

Every row in ``outputs/results.csv`` with ``is_hit=True`` and a non-empty ``matched_oracle_site_id`` (N=12). Each block recomputes the overlap calculation from the recorded ``(line_start, line_end, tolerance)`` and the oracle site ranges reconstructed in E.0.5, so any mismatch with Round 1 would be visible here.

## Hit 1: gpt-4o-mini  /  django__django-11099

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `d26b2424437dabeeca94d7900b37d2df4410da0c` |
| comment file (original) | `django/contrib/auth/validators.py` |
| comment file (normalised) | `django/contrib/auth/validators.py` |
| comment lines | 20-20 |
| matched oracle site | `site-0002` |
| oracle file | `django/contrib/auth/validators.py` |
| oracle lines | 17-23 |
| tolerance (Round 1) | 3 |
| oracle range padded | 14-26 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 0 |
| is_hit in results.csv | True |

**Message**: The regex for UnicodeUsernameValidator is the same as ASCIIUsernameValidator, which may lead to confusion.

### Distance / overlap calculation

```
comment range [20, 20]
oracle  range [17, 23]
padded  range [14, 26] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (20 >= 14) AND (20 <= 26)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    15:     flags = re.ASCII
    16: 
    17: 
    18: @deconstructible
    19: class UnicodeUsernameValidator(validators.RegexValidator):
>   20:     regex = r'^[\w.@+-]+$'
    21:     message = _(
    22:         'Enter a valid username. This value may contain only letters, '
    23:         'numbers, and @/./+/-/_ characters.'
    24:     )
    25:     flags = 0
```

### Source context (±5 lines around oracle hunk)

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

## Hit 2: gpt-4o-mini  /  django__django-11099

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `d26b2424437dabeeca94d7900b37d2df4410da0c` |
| comment file (original) | `django/contrib/auth/validators.py` |
| comment file (normalised) | `django/contrib/auth/validators.py` |
| comment lines | 25-25 |
| matched oracle site | `site-0002` |
| oracle file | `django/contrib/auth/validators.py` |
| oracle lines | 17-23 |
| tolerance (Round 1) | 3 |
| oracle range padded | 14-26 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 2 |
| is_hit in results.csv | True |

**Message**: Using flags=0 for UnicodeUsernameValidator may not handle Unicode characters correctly.

### Distance / overlap calculation

```
comment range [25, 25]
oracle  range [17, 23]
padded  range [14, 26] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (25 >= 14) AND (25 <= 26)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    20:     regex = r'^[\w.@+-]+$'
    21:     message = _(
    22:         'Enter a valid username. This value may contain only letters, '
    23:         'numbers, and @/./+/-/_ characters.'
    24:     )
>   25:     flags = 0
```

### Source context (±5 lines around oracle hunk)

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

## Hit 3: static  /  django__django-11283

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `08a4ee06510ae45562c228eefbdcaac84bd38c7a` |
| comment file (original) | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| comment file (normalised) | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| comment lines | 5-5 |
| matched oracle site | `site-0001` |
| oracle file | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| oracle lines | 1-5 |
| tolerance (Round 1) | 3 |
| oracle range padded | -2-8 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 0 |
| is_hit in results.csv | True |

**Message**: W0613: Unused argument 'schema_editor'

### Distance / overlap calculation

```
comment range [5, 5]
oracle  range [1, 5]
padded  range [-2, 8] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (5 >= -2) AND (5 <= 8)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
     1: from django.db import migrations
     2: from django.db.models import Q
     3: 
     4: 
>    5: def update_proxy_model_permissions(apps, schema_editor, reverse=False):
     6:     """
     7:     Update the content_type of proxy model permissions to use the ContentType
     8:     of the proxy model.
     9:     """
    10:     Permission = apps.get_model('auth', 'Permission')
```

### Source context (±5 lines around oracle hunk)

```
>    1: from django.db import migrations
>    2: from django.db.models import Q
>    3: 
>    4: 
>    5: def update_proxy_model_permissions(apps, schema_editor, reverse=False):
     6:     """
     7:     Update the content_type of proxy model permissions to use the ContentType
     8:     of the proxy model.
     9:     """
    10:     Permission = apps.get_model('auth', 'Permission')
```

---

## Hit 4: static  /  django__django-11283

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `08a4ee06510ae45562c228eefbdcaac84bd38c7a` |
| comment file (original) | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| comment file (normalised) | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| comment lines | 13-13 |
| matched oracle site | `site-0002` |
| oracle file | `django/contrib/auth/migrations/0011_update_proxy_permissions.py` |
| oracle lines | 7-12 |
| tolerance (Round 1) | 3 |
| oracle range padded | 4-15 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 1 |
| is_hit in results.csv | True |

**Message**: W0212: Access to a protected member _meta of a client class

### Distance / overlap calculation

```
comment range [13, 13]
oracle  range [7, 12]
padded  range [4, 15] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (13 >= 4) AND (13 <= 15)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
     8:     of the proxy model.
     9:     """
    10:     Permission = apps.get_model('auth', 'Permission')
    11:     ContentType = apps.get_model('contenttypes', 'ContentType')
    12:     for Model in apps.get_models():
>   13:         opts = Model._meta
    14:         if not opts.proxy:
    15:             continue
    16:         proxy_default_permissions_codenames = [
    17:             '%s_%s' % (action, opts.model_name)
    18:             for action in opts.default_permissions
```

### Source context (±5 lines around oracle hunk)

```
     2: from django.db.models import Q
     3: 
     4: 
     5: def update_proxy_model_permissions(apps, schema_editor, reverse=False):
     6:     """
>    7:     Update the content_type of proxy model permissions to use the ContentType
>    8:     of the proxy model.
>    9:     """
>   10:     Permission = apps.get_model('auth', 'Permission')
>   11:     ContentType = apps.get_model('contenttypes', 'ContentType')
>   12:     for Model in apps.get_models():
    13:         opts = Model._meta
    14:         if not opts.proxy:
    15:             continue
    16:         proxy_default_permissions_codenames = [
    17:             '%s_%s' % (action, opts.model_name)
```

---

## Hit 5: gpt-4o-mini  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 72-72 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 1 |
| is_hit in results.csv | True |

**Message**: Raising CommandError with a generic exception message can expose sensitive information.

### Distance / overlap calculation

```
comment range [72, 72]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (72 >= 70) AND (72 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    67:         if target is None:
    68:             top_dir = os.path.join(os.getcwd(), name)
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
>   72:                 raise CommandError("'%s' already exists" % top_dir)
    73:             except OSError as e:
    74:                 raise CommandError(e)
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
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

## Hit 6: gpt-4o-mini  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 80-80 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 0 |
| is_hit in results.csv | True |

**Message**: Raising CommandError with a generic exception message can expose sensitive information.

### Distance / overlap calculation

```
comment range [80, 80]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (80 >= 70) AND (80 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
    78:             top_dir = os.path.abspath(os.path.expanduser(target))
    79:             if not os.path.exists(top_dir):
>   80:                 raise CommandError("Destination directory '%s' does not "
    81:                                    "exist, please create it first." % top_dir)
    82: 
    83:         extensions = tuple(handle_extensions(options['extensions']))
    84:         extra_files = []
    85:         for file in options['files']:
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

## Hit 7: static  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 72-72 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 1 |
| is_hit in results.csv | True |

**Message**: B904: Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling

### Distance / overlap calculation

```
comment range [72, 72]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (72 >= 70) AND (72 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    67:         if target is None:
    68:             top_dir = os.path.join(os.getcwd(), name)
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
>   72:                 raise CommandError("'%s' already exists" % top_dir)
    73:             except OSError as e:
    74:                 raise CommandError(e)
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
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

## Hit 8: static  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 72-72 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 1 |
| is_hit in results.csv | True |

**Message**: W0707: Consider explicitly re-raising using 'except FileExistsError as exc' and 'raise CommandError("'%s' already exists" % top_dir) from exc'

### Distance / overlap calculation

```
comment range [72, 72]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (72 >= 70) AND (72 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    67:         if target is None:
    68:             top_dir = os.path.join(os.getcwd(), name)
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
>   72:                 raise CommandError("'%s' already exists" % top_dir)
    73:             except OSError as e:
    74:                 raise CommandError(e)
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
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

## Hit 9: static  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 74-74 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 0 |
| is_hit in results.csv | True |

**Message**: B904: Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling

### Distance / overlap calculation

```
comment range [74, 74]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (74 >= 70) AND (74 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
    72:                 raise CommandError("'%s' already exists" % top_dir)
    73:             except OSError as e:
>   74:                 raise CommandError(e)
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
    78:             top_dir = os.path.abspath(os.path.expanduser(target))
    79:             if not os.path.exists(top_dir):
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

## Hit 10: static  /  django__django-14382

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `29345aecf6e8d53ccb3577a3762bb0c263f7558d` |
| comment file (original) | `django/core/management/templates.py` |
| comment file (normalised) | `django/core/management/templates.py` |
| comment lines | 74-74 |
| matched oracle site | `site-0001` |
| oracle file | `django/core/management/templates.py` |
| oracle lines | 73-81 |
| tolerance (Round 1) | 3 |
| oracle range padded | 70-84 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 0 |
| is_hit in results.csv | True |

**Message**: W0707: Consider explicitly re-raising using 'raise CommandError(e) from e'

### Distance / overlap calculation

```
comment range [74, 74]
oracle  range [73, 81]
padded  range [70, 84] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (74 >= 70) AND (74 <= 84)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    69:             try:
    70:                 os.makedirs(top_dir)
    71:             except FileExistsError:
    72:                 raise CommandError("'%s' already exists" % top_dir)
    73:             except OSError as e:
>   74:                 raise CommandError(e)
    75:         else:
    76:             if app_or_project == 'app':
    77:                 self.validate_name(os.path.basename(target), 'directory')
    78:             top_dir = os.path.abspath(os.path.expanduser(target))
    79:             if not os.path.exists(top_dir):
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

## Hit 11: static  /  django__django-16816

| field | value |
|---|---|
| repo | `django/django` |
| base_commit | `191f6a9a4586b5e5f79f4f42f190e7ad4bbacc84` |
| comment file (original) | `django/contrib/admin/checks.py` |
| comment file (normalised) | `django/contrib/admin/checks.py` |
| comment lines | 913-913 |
| matched oracle site | `site-0001` |
| oracle file | `django/contrib/admin/checks.py` |
| oracle lines | 916-924 |
| tolerance (Round 1) | 3 |
| oracle range padded | 913-927 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 3 |
| is_hit in results.csv | True |

**Message**: W0212: Access to a protected member _meta of a client class

### Distance / overlap calculation

```
comment range [913, 913]
oracle  range [916, 924]
padded  range [913, 927] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (913 >= 913) AND (913 <= 927)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
   908:                         "method on '%s'."
   909:                         % (
   910:                             label,
   911:                             item,
   912:                             obj.__class__.__name__,
>  913:                             obj.model._meta.label,
   914:                         ),
   915:                         obj=obj.__class__,
   916:                         id="admin.E108",
   917:                     )
   918:                 ]
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

## Hit 12: gpt-4o-mini  /  sympy__sympy-20442

| field | value |
|---|---|
| repo | `sympy/sympy` |
| base_commit | `1abbc0ac3e552cb184317194e5d5c5b9dd8fb640` |
| comment file (original) | `sympy/physics/units/util.py` |
| comment file (normalised) | `sympy/physics/units/util.py` |
| comment lines | 28-28 |
| matched oracle site | `site-0002` |
| oracle file | `sympy/physics/units/util.py` |
| oracle lines | 30-36 |
| tolerance (Round 1) | 3 |
| oracle range padded | 27-39 |
| comment range overlaps padded oracle? | YES |
| raw distance (lines) | 2 |
| is_hit in results.csv | True |

**Message**: Using 'seen.add(i)' in a condition may lead to unexpected behavior.

### Distance / overlap calculation

```
comment range [28, 28]
oracle  range [30, 36]
padded  range [27, 39] (tolerance=3)
overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)
        = (28 >= 27) AND (28 <= 39)
        = True AND True
        = True
```

### Source context (±5 lines around comment range)

```
    23: 
    24:     if not canon_expr_units.issubset(set(canon_dim_units)):
    25:         return None
    26: 
    27:     seen = set()
>   28:     canon_dim_units = [i for i in canon_dim_units if not (i in seen or seen.add(i))]
    29: 
    30:     camat = Matrix([[dimension_system.get_dimensional_dependencies(i, mark_dimensionless=True).get(j, 0) for i in target_dims] for j in canon_dim_units])
    31:     exprmat = Matrix([dim_dependencies.get(k, 0) for k in canon_dim_units])
    32: 
    33:     res_exponents = camat.solve_least_squares(exprmat, method=None)
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

