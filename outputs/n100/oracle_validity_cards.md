# Oracle construct-validity audit cards

Stratified sample of 30 instances (sub-seed 7) from the n=100 study (seed 42).

For each oracle site, record a verdict in `oracle_validity_template.csv`:

- `bug`: the marked lines are the defect a reviewer should flag.
- `related`: part of the fix but not the core defect.
- `unrelated`: refactor, test-only, or not the defect.

`>>` in the source snippet marks the oracle lines.

## django__django-13590  (django/django)

### Issue (problem_statement)

Upgrading 2.2>3.0 causes named tuples used as arguments to __range to error.
Description
	
I noticed this while upgrading a project from 2.2 to 3.0.
This project passes named 2-tuples as arguments to range queryset filters. This works fine on 2.2. On 3.0 it causes the following error: TypeError: __new__() missing 1 required positional argument: 'far'.
This happens because django.db.models.sql.query.Query.resolve_lookup_value goes into the tuple elements to resolve lookups and then attempts to reconstitute the tuple with the resolved elements.
When it attempts to construct the new tuple it preserves the type (the named tuple) but it passes a iterator to it's constructor.
NamedTuples don't have the code path for copying an iterator, and so it errors on insufficient arguments.
The fix is to * expand the contents of the iterator into the constructor.

### Fix patch

```diff
diff --git a/django/db/models/sql/query.py b/django/db/models/sql/query.py
--- a/django/db/models/sql/query.py
+++ b/django/db/models/sql/query.py
@@ -1077,10 +1077,14 @@ def resolve_lookup_value(self, value, can_reuse, allow_joins):
         elif isinstance(value, (list, tuple)):
             # The items of the iterable may be expressions and therefore need
             # to be resolved independently.
-            return type(value)(
+            values = (
                 self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
                 for sub_value in value
             )
+            type_ = type(value)
+            if hasattr(type_, '_make'):  # namedtuple
+                return type_(*values)
+            return type_(values)
         return value
 
     def solve_lookup_type(self, lookup):
```

### Reconstructed oracle sites

- `site-0001`  django/db/models/sql/query.py:1077-1086
  ```
    1074:             value = value.resolve_expression(
    1075:                 self, reuse=can_reuse, allow_joins=allow_joins,
    1076:             )
>>  1077:         elif isinstance(value, (list, tuple)):
>>  1078:             # The items of the iterable may be expressions and therefore need
>>  1079:             # to be resolved independently.
>>  1080:             return type(value)(
>>  1081:                 self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
>>  1082:                 for sub_value in value
>>  1083:             )
>>  1084:         return value
>>  1085: 
>>  1086:     def solve_lookup_type(self, lookup):
    1087:         """
    1088:         Solve the lookup type from the lookup (e.g.: 'foobar__id__icontains').
    1089:         """
  ```

## sympy__sympy-18087  (sympy/sympy)

### Issue (problem_statement)

Simplify of simple trig expression fails
trigsimp in various versions, including 1.5, incorrectly simplifies cos(x)+sqrt(sin(x)**2) as though it were cos(x)+sin(x) for general complex x. (Oddly it gets this right if x is real.)

Embarrassingly I found this by accident while writing sympy-based teaching material...

### Fix patch

```diff
diff --git a/sympy/core/exprtools.py b/sympy/core/exprtools.py
--- a/sympy/core/exprtools.py
+++ b/sympy/core/exprtools.py
@@ -358,8 +358,8 @@ def __init__(self, factors=None):  # Factors
             for f in list(factors.keys()):
                 if isinstance(f, Rational) and not isinstance(f, Integer):
                     p, q = Integer(f.p), Integer(f.q)
-                    factors[p] = (factors[p] if p in factors else 0) + factors[f]
-                    factors[q] = (factors[q] if q in factors else 0) - factors[f]
+                    factors[p] = (factors[p] if p in factors else S.Zero) + factors[f]
+                    factors[q] = (factors[q] if q in factors else S.Zero) - factors[f]
                     factors.pop(f)
             if i:
                 factors[I] = S.One*i
@@ -448,14 +448,12 @@ def as_expr(self):  # Factors
         args = []
         for factor, exp in self.factors.items():
             if exp != 1:
-                b, e = factor.as_base_exp()
-                if isinstance(exp, int):
-                    e = _keep_coeff(Integer(exp), e)
-                elif isinstance(exp, Rational):
+                if isinstance(exp, Integer):
+                    b, e = factor.as_base_exp()
                     e = _keep_coeff(exp, e)
+                    args.append(b**e)
                 else:
-                    e *= exp
-                args.append(b**e)
+                    args.append(factor**exp)
             else:
                 args.append(factor)
         return Mul(*args)
```

### Reconstructed oracle sites

- `site-0001`  sympy/core/exprtools.py:358-365
  ```
     355:                 c.remove(I)
     356:             factors = dict(Mul._from_args(c).as_powers_dict())
     357:             # Handle all rational Coefficients
>>   358:             for f in list(factors.keys()):
>>   359:                 if isinstance(f, Rational) and not isinstance(f, Integer):
>>   360:                     p, q = Integer(f.p), Integer(f.q)
>>   361:                     factors[p] = (factors[p] if p in factors else 0) + factors[f]
>>   362:                     factors[q] = (factors[q] if q in factors else 0) - factors[f]
>>   363:                     factors.pop(f)
>>   364:             if i:
>>   365:                 factors[I] = S.One*i
     366:             if nc:
     367:                 factors[Mul(*nc, evaluate=False)] = S.One
     368:         else:
  ```
- `site-0002`  sympy/core/exprtools.py:448-461
  ```
     445: 
     446:         """
     447: 
>>   448:         args = []
>>   449:         for factor, exp in self.factors.items():
>>   450:             if exp != 1:
>>   451:                 b, e = factor.as_base_exp()
>>   452:                 if isinstance(exp, int):
>>   453:                     e = _keep_coeff(Integer(exp), e)
>>   454:                 elif isinstance(exp, Rational):
>>   455:                     e = _keep_coeff(exp, e)
>>   456:                 else:
>>   457:                     e *= exp
>>   458:                 args.append(b**e)
>>   459:             else:
>>   460:                 args.append(factor)
>>   461:         return Mul(*args)
     462: 
     463:     def mul(self, other):  # Factors
     464:         """Return Factors of ``self * other``.
  ```

## pytest-dev__pytest-5103  (pytest-dev/pytest)

### Issue (problem_statement)

Unroll the iterable for all/any calls to get better reports
Sometime I need to assert some predicate on all of an iterable, and for that the builtin functions `all`/`any` are great - but the failure messages aren't useful at all!
For example - the same test written in three ways:

- A generator expression
```sh                                                                                                                                                                                                                         
    def test_all_even():
        even_stevens = list(range(1,100,2))
>       assert all(is_even(number) for number in even_stevens)
E       assert False
E        +  where False = all(<generator object test_all_even.<locals>.<genexpr> at 0x101f82ed0>)
```
- A list comprehension
```sh
    def test_all_even():
        even_stevens = list(range(1,100,2))
>       assert all([is_even(number) for number in even_stevens])
E       assert False
E        +  where False = all([False, False, False, False, False, False, ...])
```
- A for loop
```sh
    def test_all_even():
        even_stevens = list(range(1,100,2))
        for number in even_stevens:
>           assert is_even(number)
E           assert False
E            +  where False = is_even(1)

test_all_any.py:7: AssertionError
```
The only one that gives a meaningful report is the for loop - but it's way more wordy, and `all` asserts don't translate to a for loop nicely (I'll have to write a `break` or a helper function - yuck)
I propose the assertion re-writer "unrolls" the iterator to the third form, and then uses the already existing reports.

- [x] Include a detailed description of the bug or suggestion
- [x] `pip list` of the virtual environment you are using
```
Package        Version
-------------- -------
atomicwrites   1.3.0  
attrs          19.1.0 
more-itertools 7.0.0  
pip            19.0.3 
pluggy         0.9.0  
py             1.8.0  
pytest    
[... truncated ...]

### Fix patch

```diff
diff --git a/src/_pytest/assertion/rewrite.py b/src/_pytest/assertion/rewrite.py
--- a/src/_pytest/assertion/rewrite.py
+++ b/src/_pytest/assertion/rewrite.py
@@ -964,6 +964,8 @@ def visit_Call_35(self, call):
         """
         visit `ast.Call` nodes on Python3.5 and after
         """
+        if isinstance(call.func, ast.Name) and call.func.id == "all":
+            return self._visit_all(call)
         new_func, func_expl = self.visit(call.func)
         arg_expls = []
         new_args = []
@@ -987,6 +989,27 @@ def visit_Call_35(self, call):
         outer_expl = "%s\n{%s = %s\n}" % (res_expl, res_expl, expl)
         return res, outer_expl
 
+    def _visit_all(self, call):
+        """Special rewrite for the builtin all function, see #5062"""
+        if not isinstance(call.args[0], (ast.GeneratorExp, ast.ListComp)):
+            return
+        gen_exp = call.args[0]
+        assertion_module = ast.Module(
+            body=[ast.Assert(test=gen_exp.elt, lineno=1, msg="", col_offset=1)]
+        )
+        AssertionRewriter(module_path=None, config=None).run(assertion_module)
+        for_loop = ast.For(
+            iter=gen_exp.generators[0].iter,
+            target=gen_exp.generators[0].target,
+            body=assertion_module.body,
+            orelse=[],
+        )
+        self.statements.append(for_loop)
+        return (
+            ast.Num(n=1),
+            "",
+        )  # Return an empty expression, all the asserts are in the for_loop
+
     def visit_Starred(self, starred):
         # From Python 3.5, a Starred node can appear in a function call
         res, expl = self.visit(starred.value)
@@ -997,6 +1020,8 @@ def visit_Call_legacy(self, call):
         """
         visit `ast.Call nodes on 3.4 and below`
         """
+        if isinstance(call.func, ast.Name) and call.func.id == "all":
+            return self._visit_all(call)
         new_func, func_expl = self.visit(call.func)
         arg_expls = []
         new_args = []
```

### Reconstructed oracle sites

- `site-0001`  src/_pytest/assertion/rewrite.py:964-969
  ```
     961:         left_expr, left_expl = self.visit(binop.left)
     962:         right_expr, right_expl = self.visit(binop.right)
     963:         explanation = "(%s %s %s)" % (left_expl, symbol, right_expl)
>>   964:         res = self.assign(ast.BinOp(left_expr, binop.op, right_expr))
>>   965:         return res, explanation
>>   966: 
>>   967:     def visit_Call_35(self, call):
>>   968:         """
>>   969:         visit `ast.Call` nodes on Python3.5 and after
     970:         """
     971:         new_func, func_expl = self.visit(call.func)
     972:         arg_expls = []
  ```
- `site-0002`  src/_pytest/assertion/rewrite.py:987-992
  ```
     984:             else:  # **args have `arg` keywords with an .arg of None
     985:                 arg_expls.append("**" + expl)
     986: 
>>   987:         expl = "%s(%s)" % (func_expl, ", ".join(arg_expls))
>>   988:         new_call = ast.Call(new_func, new_args, new_kwargs)
>>   989:         res = self.assign(new_call)
>>   990:         res_expl = self.explanation_param(self.display(res))
>>   991:         outer_expl = "%s\n{%s = %s\n}" % (res_expl, res_expl, expl)
>>   992:         return res, outer_expl
     993: 
     994:     def visit_Starred(self, starred):
     995:         # From Python 3.5, a Starred node can appear in a function call
  ```
- `site-0003`  src/_pytest/assertion/rewrite.py:997-1002
  ```
     994:     def visit_Starred(self, starred):
     995:         # From Python 3.5, a Starred node can appear in a function call
     996:         res, expl = self.visit(starred.value)
>>   997:         new_starred = ast.Starred(res, starred.ctx)
>>   998:         return new_starred, "*" + expl
>>   999: 
>>  1000:     def visit_Call_legacy(self, call):
>>  1001:         """
>>  1002:         visit `ast.Call nodes on 3.4 and below`
    1003:         """
    1004:         new_func, func_expl = self.visit(call.func)
    1005:         arg_expls = []
  ```

## scikit-learn__scikit-learn-13497  (scikit-learn/scikit-learn)

### Issue (problem_statement)

Comparing string to array in _estimate_mi
In ``_estimate_mi`` there is ``discrete_features == 'auto'`` but discrete features can be an array of indices or a boolean mask.
This will error in future versions of numpy.
Also this means we never test this function with discrete features != 'auto', it seems?

### Fix patch

```diff
diff --git a/sklearn/feature_selection/mutual_info_.py b/sklearn/feature_selection/mutual_info_.py
--- a/sklearn/feature_selection/mutual_info_.py
+++ b/sklearn/feature_selection/mutual_info_.py
@@ -10,7 +10,7 @@
 from ..preprocessing import scale
 from ..utils import check_random_state
 from ..utils.fixes import _astype_copy_false
-from ..utils.validation import check_X_y
+from ..utils.validation import check_array, check_X_y
 from ..utils.multiclass import check_classification_targets
 
 
@@ -247,14 +247,16 @@ def _estimate_mi(X, y, discrete_features='auto', discrete_target=False,
     X, y = check_X_y(X, y, accept_sparse='csc', y_numeric=not discrete_target)
     n_samples, n_features = X.shape
 
-    if discrete_features == 'auto':
-        discrete_features = issparse(X)
-
-    if isinstance(discrete_features, bool):
+    if isinstance(discrete_features, (str, bool)):
+        if isinstance(discrete_features, str):
+            if discrete_features == 'auto':
+                discrete_features = issparse(X)
+            else:
+                raise ValueError("Invalid string value for discrete_features.")
         discrete_mask = np.empty(n_features, dtype=bool)
         discrete_mask.fill(discrete_features)
     else:
-        discrete_features = np.asarray(discrete_features)
+        discrete_features = check_array(discrete_features, ensure_2d=False)
         if discrete_features.dtype != 'bool':
             discrete_mask = np.zeros(n_features, dtype=bool)
             discrete_mask[discrete_features] = True
```

### Reconstructed oracle sites

- `site-0001`  sklearn/feature_selection/mutual_info_.py:10-16
  ```
       7: 
       8: from ..metrics.cluster.supervised import mutual_info_score
       9: from ..neighbors import NearestNeighbors
>>    10: from ..preprocessing import scale
>>    11: from ..utils import check_random_state
>>    12: from ..utils.fixes import _astype_copy_false
>>    13: from ..utils.validation import check_X_y
>>    14: from ..utils.multiclass import check_classification_targets
>>    15: 
>>    16: 
      17: def _compute_mi_cc(x, y, n_neighbors):
      18:     """Compute mutual information between two continuous variables.
      19: 
  ```
- `site-0002`  sklearn/feature_selection/mutual_info_.py:247-260
  ```
     244:     .. [2] B. C. Ross "Mutual Information between Discrete and Continuous
     245:            Data Sets". PLoS ONE 9(2), 2014.
     246:     """
>>   247:     X, y = check_X_y(X, y, accept_sparse='csc', y_numeric=not discrete_target)
>>   248:     n_samples, n_features = X.shape
>>   249: 
>>   250:     if discrete_features == 'auto':
>>   251:         discrete_features = issparse(X)
>>   252: 
>>   253:     if isinstance(discrete_features, bool):
>>   254:         discrete_mask = np.empty(n_features, dtype=bool)
>>   255:         discrete_mask.fill(discrete_features)
>>   256:     else:
>>   257:         discrete_features = np.asarray(discrete_features)
>>   258:         if discrete_features.dtype != 'bool':
>>   259:             discrete_mask = np.zeros(n_features, dtype=bool)
>>   260:             discrete_mask[discrete_features] = True
     261:         else:
     262:             discrete_mask = discrete_features
     263: 
  ```

## matplotlib__matplotlib-25079  (matplotlib/matplotlib)

### Issue (problem_statement)

[Bug]: Setting norm with existing colorbar fails with 3.6.3
### Bug summary

Setting the norm to a `LogNorm` after the colorbar has been created (e.g. in interactive code) fails with an `Invalid vmin` value in matplotlib 3.6.3.

The same code worked in previous matplotlib versions.

Not that vmin and vmax are explicitly set to values valid for `LogNorm` and no negative values (or values == 0) exist in the input data.

### Code for reproduction

```python
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

# create some random data to fill a 2d plot
rng = np.random.default_rng(0)
img = rng.uniform(1, 5, (25, 25))

# plot it
fig, ax = plt.subplots(layout="constrained")
plot = ax.pcolormesh(img)
cbar = fig.colorbar(plot, ax=ax)

vmin = 1
vmax = 5

plt.ion()
fig.show()
plt.pause(0.5)

plot.norm = LogNorm(vmin, vmax)
plot.autoscale()
plt.pause(0.5)
```


### Actual outcome

```
Traceback (most recent call last):
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/backends/backend_qt.py", line 454, in _draw_idle
    self.draw()
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/backends/backend_agg.py", line 405, in draw
    self.figure.draw(self.renderer)
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/artist.py", line 74, in draw_wrapper
    result = draw(artist, renderer, *args, **kwargs)
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/artist.py", line 51, in draw_wrapper
    return draw(artist, renderer)
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/figure.py", line 3082, in draw
    mimage._draw_list_compositing_images(
  File "/home/mnoethe/.local/conda/envs/cta-dev/lib/python3.9/site-packages/matplotlib/image.py", line 131, in _draw_list_compositing_images
    a.draw(renderer)
  File "/hom
[... truncated ...]

### Fix patch

```diff
diff --git a/lib/matplotlib/colors.py b/lib/matplotlib/colors.py
--- a/lib/matplotlib/colors.py
+++ b/lib/matplotlib/colors.py
@@ -1362,8 +1362,12 @@ def inverse(self, value):
 
     def autoscale(self, A):
         """Set *vmin*, *vmax* to min, max of *A*."""
-        self.vmin = self.vmax = None
-        self.autoscale_None(A)
+        with self.callbacks.blocked():
+            # Pause callbacks while we are updating so we only get
+            # a single update signal at the end
+            self.vmin = self.vmax = None
+            self.autoscale_None(A)
+        self._changed()
 
     def autoscale_None(self, A):
         """If vmin or vmax are not set, use the min/max of *A* to set them."""
```

### Reconstructed oracle sites

- `site-0001`  lib/matplotlib/colors.py:1362-1369
  ```
    1359:             return vmin + val * (vmax - vmin)
    1360:         else:
    1361:             return vmin + value * (vmax - vmin)
>>  1362: 
>>  1363:     def autoscale(self, A):
>>  1364:         """Set *vmin*, *vmax* to min, max of *A*."""
>>  1365:         self.vmin = self.vmax = None
>>  1366:         self.autoscale_None(A)
>>  1367: 
>>  1368:     def autoscale_None(self, A):
>>  1369:         """If vmin or vmax are not set, use the min/max of *A* to set them."""
    1370:         A = np.asanyarray(A)
    1371:         if self.vmin is None and A.size:
    1372:             self.vmin = A.min()
  ```

## sphinx-doc__sphinx-8273  (sphinx-doc/sphinx)

### Issue (problem_statement)

Generate man page section directories
**Current man page generation does not conform to `MANPATH` search functionality**
Currently, all generated man pages are placed in to a single-level directory: `<build-dir>/man`. Unfortunately, this cannot be used in combination with the unix `MANPATH` environment variable. The `man` program explicitly looks for man pages in section directories (such as `man/man1`, etc.). 

**Describe the solution you'd like**
It would be great if sphinx would automatically create the section directories (e.g., `man/man1/`, `man/man3/`, etc.) and place each generated man page within appropriate section.

**Describe alternatives you've considered**
This problem can be over come within our project’s build system, ensuring the built man pages are installed in a correct location, but it would be nice if the build directory had the proper layout.

I’m happy to take a crack at implementing a fix, though this change in behavior may break some people who expect everything to appear in a `man/` directory.

### Fix patch

```diff
diff --git a/sphinx/builders/manpage.py b/sphinx/builders/manpage.py
--- a/sphinx/builders/manpage.py
+++ b/sphinx/builders/manpage.py
@@ -24,7 +24,7 @@
 from sphinx.util import progress_message
 from sphinx.util.console import darkgreen  # type: ignore
 from sphinx.util.nodes import inline_all_toctrees
-from sphinx.util.osutil import make_filename_from_project
+from sphinx.util.osutil import ensuredir, make_filename_from_project
 from sphinx.writers.manpage import ManualPageWriter, ManualPageTranslator
 
 
@@ -80,7 +80,12 @@ def write(self, *ignored: Any) -> None:
             docsettings.authors = authors
             docsettings.section = section
 
-            targetname = '%s.%s' % (name, section)
+            if self.config.man_make_section_directory:
+                ensuredir(path.join(self.outdir, str(section)))
+                targetname = '%s/%s.%s' % (section, name, section)
+            else:
+                targetname = '%s.%s' % (name, section)
+
             logger.info(darkgreen(targetname) + ' { ', nonl=True)
             destination = FileOutput(
                 destination_path=path.join(self.outdir, targetname),
@@ -115,6 +120,7 @@ def setup(app: Sphinx) -> Dict[str, Any]:
 
     app.add_config_value('man_pages', default_man_pages, None)
     app.add_config_value('man_show_urls', False, None)
+    app.add_config_value('man_make_section_directory', False, None)
 
     return {
         'version': 'builtin',
```

### Reconstructed oracle sites

- `site-0001`  sphinx/builders/manpage.py:24-30
  ```
      21: from sphinx.errors import NoUri
      22: from sphinx.locale import __
      23: from sphinx.util import logging
>>    24: from sphinx.util import progress_message
>>    25: from sphinx.util.console import darkgreen  # type: ignore
>>    26: from sphinx.util.nodes import inline_all_toctrees
>>    27: from sphinx.util.osutil import make_filename_from_project
>>    28: from sphinx.writers.manpage import ManualPageWriter, ManualPageTranslator
>>    29: 
>>    30: 
      31: logger = logging.getLogger(__name__)
      32: 
      33: 
  ```
- `site-0002`  sphinx/builders/manpage.py:80-86
  ```
      77: 
      78:             docsettings.title = name
      79:             docsettings.subtitle = description
>>    80:             docsettings.authors = authors
>>    81:             docsettings.section = section
>>    82: 
>>    83:             targetname = '%s.%s' % (name, section)
>>    84:             logger.info(darkgreen(targetname) + ' { ', nonl=True)
>>    85:             destination = FileOutput(
>>    86:                 destination_path=path.join(self.outdir, targetname),
      87:                 encoding='utf-8')
      88: 
      89:             tree = self.env.get_doctree(docname)
  ```
- `site-0003`  sphinx/builders/manpage.py:115-120
  ```
     112: 
     113: def setup(app: Sphinx) -> Dict[str, Any]:
     114:     app.add_builder(ManualPageBuilder)
>>   115: 
>>   116:     app.add_config_value('man_pages', default_man_pages, None)
>>   117:     app.add_config_value('man_show_urls', False, None)
>>   118: 
>>   119:     return {
>>   120:         'version': 'builtin',
     121:         'parallel_read_safe': True,
     122:         'parallel_write_safe': True,
     123:     }
  ```

## pylint-dev__pylint-7080  (pylint-dev/pylint)

### Issue (problem_statement)

`--recursive=y` ignores `ignore-paths`
### Bug description

When running recursively, it seems `ignore-paths` in my settings in pyproject.toml is completely ignored

### Configuration

```ini
[tool.pylint.MASTER]
ignore-paths = [
  # Auto generated
  "^src/gen/.*$",
]
```


### Command used

```shell
pylint --recursive=y src/
```


### Pylint output

```shell
************* Module region_selection
src\region_selection.py:170:0: R0914: Too many local variables (17/15) (too-many-locals)
************* Module about
src\gen\about.py:2:0: R2044: Line with empty comment (empty-comment)
src\gen\about.py:4:0: R2044: Line with empty comment (empty-comment)
src\gen\about.py:57:0: C0301: Line too long (504/120) (line-too-long)
src\gen\about.py:12:0: C0103: Class name "Ui_AboutAutoSplitWidget" doesn't conform to '_?_?[a-zA-Z]+?$' pattern (invalid-name)
src\gen\about.py:12:0: R0205: Class 'Ui_AboutAutoSplitWidget' inherits from object, can be safely removed from bases in python3 (useless-object-inheritance)
src\gen\about.py:13:4: C0103: Method name "setupUi" doesn't conform to snake_case naming style (invalid-name)
src\gen\about.py:13:22: C0103: Argument name "AboutAutoSplitWidget" doesn't conform to snake_case naming style (invalid-name)
src\gen\about.py:53:4: C0103: Method name "retranslateUi" doesn't conform to snake_case naming style (invalid-name)
src\gen\about.py:53:28: C0103: Argument name "AboutAutoSplitWidget" doesn't conform to snake_case naming style (invalid-name)
src\gen\about.py:24:8: W0201: Attribute 'ok_button' defined outside __init__ (attribute-defined-outside-init)
src\gen\about.py:27:8: W0201: Attribute 'created_by_label' defined outside __init__ (attribute-defined-outside-init)
src\gen\about.py:30:8: W0201: Attribute 'version_label' defined outside __init__ (attribute-defined-outside-init)
src\gen\about.py:33:8: W0201: Attribute 'donate_text_label' defined outside __init__ (attribute-defined-outside-init)
src\gen\about.
[... truncated ...]

### Fix patch

```diff
diff --git a/pylint/lint/expand_modules.py b/pylint/lint/expand_modules.py
--- a/pylint/lint/expand_modules.py
+++ b/pylint/lint/expand_modules.py
@@ -52,6 +52,7 @@ def _is_ignored_file(
     ignore_list_re: list[Pattern[str]],
     ignore_list_paths_re: list[Pattern[str]],
 ) -> bool:
+    element = os.path.normpath(element)
     basename = os.path.basename(element)
     return (
         basename in ignore_list
```

### Reconstructed oracle sites

- `site-0001`  pylint/lint/expand_modules.py:52-57
  ```
      49: def _is_ignored_file(
      50:     element: str,
      51:     ignore_list: list[str],
>>    52:     ignore_list_re: list[Pattern[str]],
>>    53:     ignore_list_paths_re: list[Pattern[str]],
>>    54: ) -> bool:
>>    55:     basename = os.path.basename(element)
>>    56:     return (
>>    57:         basename in ignore_list
      58:         or _is_in_ignore_list_re(basename, ignore_list_re)
      59:         or _is_in_ignore_list_re(element, ignore_list_paths_re)
      60:     )
  ```

## psf__requests-863  (psf/requests)

### Issue (problem_statement)

Allow lists in the dict values of the hooks argument
Currently the Request class has a .register_hook() method but it parses the dictionary it expects from it's hooks argument weirdly: the argument can only specify one hook function per hook.  If you pass in a list of hook functions per hook the code in Request.**init**() will wrap the list in a list which then fails when the hooks are consumed (since a list is not callable).  This is especially annoying since you can not use multiple hooks from a session.  The only way to get multiple hooks now is to create the request object without sending it, then call .register_hook() multiple times and then finally call .send().

This would all be much easier if Request.**init**() parsed the hooks parameter in a way that it accepts lists as it's values.

### Fix patch

```diff
diff --git a/requests/models.py b/requests/models.py
--- a/requests/models.py
+++ b/requests/models.py
@@ -462,8 +462,10 @@ def path_url(self):
 
     def register_hook(self, event, hook):
         """Properly register a hook."""
-
-        self.hooks[event].append(hook)
+        if isinstance(hook, (list, tuple, set)):
+            self.hooks[event].extend(hook)
+        else:
+            self.hooks[event].append(hook)
 
     def deregister_hook(self, event, hook):
         """Deregister a previously registered hook.
```

### Reconstructed oracle sites

- `site-0001`  requests/models.py:462-469
  ```
     459:             url.append(query)
     460: 
     461:         return ''.join(url)
>>   462: 
>>   463:     def register_hook(self, event, hook):
>>   464:         """Properly register a hook."""
>>   465: 
>>   466:         self.hooks[event].append(hook)
>>   467: 
>>   468:     def deregister_hook(self, event, hook):
>>   469:         """Deregister a previously registered hook.
     470:         Returns True if the hook existed, False if not.
     471:         """
     472: 
  ```

## astropy__astropy-14995  (astropy/astropy)

### Issue (problem_statement)

In v5.3, NDDataRef mask propagation fails when one of the operand does not have a mask
### Description

This applies to v5.3. 

It looks like when one of the operand does not have a mask, the mask propagation when doing arithmetic, in particular with `handle_mask=np.bitwise_or` fails.  This is not a problem in v5.2.

I don't know enough about how all that works, but it seems from the error that the operand without a mask is set as a mask of None's and then the bitwise_or tries to operate on an integer and a None and fails.

### Expected behavior

When one of the operand does not have mask, the mask that exists should just be copied over to the output.  Or whatever was done in that situation in v5.2 where there's no problem.

### How to Reproduce

This is with v5.3.   With v5.2, there are no errors.

```
>>> import numpy as np
>>> from astropy.nddata import NDDataRef

>>> array = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
>>> mask = np.array([[0, 1, 64], [8, 0, 1], [2, 1, 0]])

>>> nref_nomask = NDDataRef(array)
>>> nref_mask = NDDataRef(array, mask=mask)

# multiply no mask by constant (no mask * no mask)
>>> nref_nomask.multiply(1., handle_mask=np.bitwise_or).mask   # returns nothing, no mask,  OK

# multiply no mask by itself (no mask * no mask)
>>> nref_nomask.multiply(nref_nomask, handle_mask=np.bitwise_or).mask # return nothing, no mask, OK

# multiply mask by constant (mask * no mask)
>>> nref_mask.multiply(1., handle_mask=np.bitwise_or).mask
...
TypeError: unsupported operand type(s) for |: 'int' and 'NoneType'

# multiply mask by itself (mask * mask)
>>> nref_mask.multiply(nref_mask, handle_mask=np.bitwise_or).mask
array([[ 0,  1, 64],
       [ 8,  0,  1],
       [ 2,  1,  0]])

# multiply mask by no mask (mask * no mask)
>>> nref_mask.multiply(nref_nomask, handle_mask=np.bitwise_or).mask
...
TypeError: unsupported operand type(s) for |: 'int' and 'NoneType'
```


### Versions

>>> import sys; print("Python", sys.versio
[... truncated ...]

### Fix patch

```diff
diff --git a/astropy/nddata/mixins/ndarithmetic.py b/astropy/nddata/mixins/ndarithmetic.py
--- a/astropy/nddata/mixins/ndarithmetic.py
+++ b/astropy/nddata/mixins/ndarithmetic.py
@@ -520,10 +520,10 @@ def _arithmetic_mask(self, operation, operand, handle_mask, axis=None, **kwds):
         elif self.mask is None and operand is not None:
             # Make a copy so there is no reference in the result.
             return deepcopy(operand.mask)
-        elif operand is None:
+        elif operand.mask is None:
             return deepcopy(self.mask)
         else:
-            # Now lets calculate the resulting mask (operation enforces copy)
+            # Now let's calculate the resulting mask (operation enforces copy)
             return handle_mask(self.mask, operand.mask, **kwds)
 
     def _arithmetic_wcs(self, operation, operand, compare_wcs, **kwds):
```

### Reconstructed oracle sites

- `site-0001`  astropy/nddata/mixins/ndarithmetic.py:520-529
  ```
     517:             self.mask is None and operand is not None and operand.mask is None
     518:         ) or handle_mask is None:
     519:             return None
>>   520:         elif self.mask is None and operand is not None:
>>   521:             # Make a copy so there is no reference in the result.
>>   522:             return deepcopy(operand.mask)
>>   523:         elif operand is None:
>>   524:             return deepcopy(self.mask)
>>   525:         else:
>>   526:             # Now lets calculate the resulting mask (operation enforces copy)
>>   527:             return handle_mask(self.mask, operand.mask, **kwds)
>>   528: 
>>   529:     def _arithmetic_wcs(self, operation, operand, compare_wcs, **kwds):
     530:         """
     531:         Calculate the resulting wcs.
     532: 
  ```

## pallets__flask-4045  (pallets/flask)

### Issue (problem_statement)

Raise error when blueprint name contains a dot
This is required since every dot is now significant since blueprints can be nested. An error was already added for endpoint names in 1.0, but should have been added for this as well.

### Fix patch

```diff
diff --git a/src/flask/blueprints.py b/src/flask/blueprints.py
--- a/src/flask/blueprints.py
+++ b/src/flask/blueprints.py
@@ -188,6 +188,10 @@ def __init__(
             template_folder=template_folder,
             root_path=root_path,
         )
+
+        if "." in name:
+            raise ValueError("'name' may not contain a dot '.' character.")
+
         self.name = name
         self.url_prefix = url_prefix
         self.subdomain = subdomain
@@ -360,12 +364,12 @@ def add_url_rule(
         """Like :meth:`Flask.add_url_rule` but for a blueprint.  The endpoint for
         the :func:`url_for` function is prefixed with the name of the blueprint.
         """
-        if endpoint:
-            assert "." not in endpoint, "Blueprint endpoints should not contain dots"
-        if view_func and hasattr(view_func, "__name__"):
-            assert (
-                "." not in view_func.__name__
-            ), "Blueprint view function name should not contain dots"
+        if endpoint and "." in endpoint:
+            raise ValueError("'endpoint' may not contain a dot '.' character.")
+
+        if view_func and hasattr(view_func, "__name__") and "." in view_func.__name__:
+            raise ValueError("'view_func' name may not contain a dot '.' character.")
+
         self.record(lambda s: s.add_url_rule(rule, endpoint, view_func, **options))
 
     def app_template_filter(self, name: t.Optional[str] = None) -> t.Callable:
```

### Reconstructed oracle sites

- `site-0001`  src/flask/blueprints.py:188-193
  ```
     185:             import_name=import_name,
     186:             static_folder=static_folder,
     187:             static_url_path=static_url_path,
>>   188:             template_folder=template_folder,
>>   189:             root_path=root_path,
>>   190:         )
>>   191:         self.name = name
>>   192:         self.url_prefix = url_prefix
>>   193:         self.subdomain = subdomain
     194:         self.deferred_functions: t.List[DeferredSetupFunction] = []
     195: 
     196:         if url_defaults is None:
  ```
- `site-0002`  src/flask/blueprints.py:360-371
  ```
     357:         view_func: t.Optional[t.Callable] = None,
     358:         **options: t.Any,
     359:     ) -> None:
>>   360:         """Like :meth:`Flask.add_url_rule` but for a blueprint.  The endpoint for
>>   361:         the :func:`url_for` function is prefixed with the name of the blueprint.
>>   362:         """
>>   363:         if endpoint:
>>   364:             assert "." not in endpoint, "Blueprint endpoints should not contain dots"
>>   365:         if view_func and hasattr(view_func, "__name__"):
>>   366:             assert (
>>   367:                 "." not in view_func.__name__
>>   368:             ), "Blueprint view function name should not contain dots"
>>   369:         self.record(lambda s: s.add_url_rule(rule, endpoint, view_func, **options))
>>   370: 
>>   371:     def app_template_filter(self, name: t.Optional[str] = None) -> t.Callable:
     372:         """Register a custom template filter, available application wide.  Like
     373:         :meth:`Flask.template_filter` but for a blueprint.
     374: 
  ```

## django__django-15498  (django/django)

### Issue (problem_statement)

Fix handling empty string for If-Modified-Since header
Description
	
Empty string used to be ignored for If-Modified-Since header, but now raises exception since d6aff369ad3.
Fix handling empty string for If-Modified-Since header
Description
	
Empty string used to be ignored for If-Modified-Since header, but now raises exception since d6aff369ad3.

### Fix patch

```diff
diff --git a/django/views/static.py b/django/views/static.py
--- a/django/views/static.py
+++ b/django/views/static.py
@@ -129,12 +129,14 @@ def was_modified_since(header=None, mtime=0, size=0):
         if header is None:
             raise ValueError
         matches = re.match(r"^([^;]+)(; length=([0-9]+))?$", header, re.IGNORECASE)
+        if matches is None:
+            raise ValueError
         header_mtime = parse_http_date(matches[1])
         header_len = matches[3]
         if header_len and int(header_len) != size:
             raise ValueError
         if int(mtime) > header_mtime:
             raise ValueError
-    except (AttributeError, ValueError, OverflowError):
+    except (ValueError, OverflowError):
         return True
     return False
```

### Reconstructed oracle sites

- `site-0001`  django/views/static.py:129-140
  ```
     126:       This is the size of the item we're talking about.
     127:     """
     128:     try:
>>   129:         if header is None:
>>   130:             raise ValueError
>>   131:         matches = re.match(r"^([^;]+)(; length=([0-9]+))?$", header, re.IGNORECASE)
>>   132:         header_mtime = parse_http_date(matches[1])
>>   133:         header_len = matches[3]
>>   134:         if header_len and int(header_len) != size:
>>   135:             raise ValueError
>>   136:         if int(mtime) > header_mtime:
>>   137:             raise ValueError
>>   138:     except (AttributeError, ValueError, OverflowError):
>>   139:         return True
>>   140:     return False
  ```

## sympy__sympy-23117  (sympy/sympy)

### Issue (problem_statement)

sympy.Array([]) fails, while sympy.Matrix([]) works
SymPy 1.4 does not allow to construct empty Array (see code below). Is this the intended behavior?

```
>>> import sympy
KeyboardInterrupt
>>> import sympy
>>> from sympy import Array
>>> sympy.__version__
'1.4'
>>> a = Array([])
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/hcui7/miniconda3/envs/a/lib/python3.7/site-packages/sympy/tensor/array/dense_ndim_array.py", line 130, in __new__
    return cls._new(iterable, shape, **kwargs)
  File "/Users/hcui7/miniconda3/envs/a/lib/python3.7/site-packages/sympy/tensor/array/dense_ndim_array.py", line 136, in _new
    shape, flat_list = cls._handle_ndarray_creation_inputs(iterable, shape, **kwargs)
  File "/Users/hcui7/miniconda3/envs/a/lib/python3.7/site-packages/sympy/tensor/array/ndim_array.py", line 142, in _handle_ndarray_creation_inputs
    iterable, shape = cls._scan_iterable_shape(iterable)
  File "/Users/hcui7/miniconda3/envs/a/lib/python3.7/site-packages/sympy/tensor/array/ndim_array.py", line 127, in _scan_iterable_shape
    return f(iterable)
  File "/Users/hcui7/miniconda3/envs/a/lib/python3.7/site-packages/sympy/tensor/array/ndim_array.py", line 120, in f
    elems, shapes = zip(*[f(i) for i in pointer])
ValueError: not enough values to unpack (expected 2, got 0)
```

@czgdp1807

### Fix patch

```diff
diff --git a/sympy/tensor/array/ndim_array.py b/sympy/tensor/array/ndim_array.py
--- a/sympy/tensor/array/ndim_array.py
+++ b/sympy/tensor/array/ndim_array.py
@@ -145,10 +145,12 @@ def __new__(cls, iterable, shape=None, **kwargs):
 
     def _parse_index(self, index):
         if isinstance(index, (SYMPY_INTS, Integer)):
-            raise ValueError("Only a tuple index is accepted")
+            if index >= self._loop_size:
+                raise ValueError("Only a tuple index is accepted")
+            return index
 
         if self._loop_size == 0:
-            raise ValueError("Index not valide with an empty array")
+            raise ValueError("Index not valid with an empty array")
 
         if len(index) != self._rank:
             raise ValueError('Wrong number of array axes')
@@ -194,6 +196,9 @@ def f(pointer):
             if not isinstance(pointer, Iterable):
                 return [pointer], ()
 
+            if len(pointer) == 0:
+                return [], (0,)
+
             result = []
             elems, shapes = zip(*[f(i) for i in pointer])
             if len(set(shapes)) != 1:
@@ -567,11 +572,11 @@ def _check_special_bounds(cls, flat_list, shape):
 
     def _check_index_for_getitem(self, index):
         if isinstance(index, (SYMPY_INTS, Integer, slice)):
-            index = (index, )
+            index = (index,)
 
         if len(index) < self.rank():
-            index = tuple([i for i in index] + \
-                          [slice(None) for i in range(len(index), self.rank())])
+            index = tuple(index) + \
+                          tuple(slice(None) for i in range(len(index), self.rank()))
 
         if len(index) > self.rank():
             raise ValueError('Dimension of index greater than rank of array')
```

### Reconstructed oracle sites

- `site-0001`  sympy/tensor/array/ndim_array.py:145-154
  ```
     142:     def __new__(cls, iterable, shape=None, **kwargs):
     143:         from sympy.tensor.array import ImmutableDenseNDimArray
     144:         return ImmutableDenseNDimArray(iterable, shape, **kwargs)
>>   145: 
>>   146:     def _parse_index(self, index):
>>   147:         if isinstance(index, (SYMPY_INTS, Integer)):
>>   148:             raise ValueError("Only a tuple index is accepted")
>>   149: 
>>   150:         if self._loop_size == 0:
>>   151:             raise ValueError("Index not valide with an empty array")
>>   152: 
>>   153:         if len(index) != self._rank:
>>   154:             raise ValueError('Wrong number of array axes')
     155: 
     156:         real_index = 0
     157:         # check if input index can exist in current indexing
  ```
- `site-0002`  sympy/tensor/array/ndim_array.py:194-199
  ```
     191:     @classmethod
     192:     def _scan_iterable_shape(cls, iterable):
     193:         def f(pointer):
>>   194:             if not isinstance(pointer, Iterable):
>>   195:                 return [pointer], ()
>>   196: 
>>   197:             result = []
>>   198:             elems, shapes = zip(*[f(i) for i in pointer])
>>   199:             if len(set(shapes)) != 1:
     200:                 raise ValueError("could not determine shape unambiguously")
     201:             for i in elems:
     202:                 result.extend(i)
  ```
- `site-0003`  sympy/tensor/array/ndim_array.py:567-577
  ```
     564:             raise ValueError("arrays without shape need one scalar value")
     565:         if shape == (0,) and len(flat_list) > 0:
     566:             raise ValueError("if array shape is (0,) there cannot be elements")
>>   567: 
>>   568:     def _check_index_for_getitem(self, index):
>>   569:         if isinstance(index, (SYMPY_INTS, Integer, slice)):
>>   570:             index = (index, )
>>   571: 
>>   572:         if len(index) < self.rank():
>>   573:             index = tuple([i for i in index] + \
>>   574:                           [slice(None) for i in range(len(index), self.rank())])
>>   575: 
>>   576:         if len(index) > self.rank():
>>   577:             raise ValueError('Dimension of index greater than rank of array')
     578: 
     579:         return index
     580: 
  ```

## pytest-dev__pytest-7168  (pytest-dev/pytest)

### Issue (problem_statement)

INTERNALERROR when exception in __repr__
Minimal code to reproduce the issue: 
```python
class SomeClass:
    def __getattribute__(self, attr):
        raise
    def __repr__(self):
        raise
def test():
    SomeClass().attr
```
Session traceback:
```
============================= test session starts ==============================
platform darwin -- Python 3.8.1, pytest-5.4.1, py-1.8.1, pluggy-0.13.1 -- /usr/local/opt/python@3.8/bin/python3.8
cachedir: .pytest_cache
rootdir: ******
plugins: asyncio-0.10.0, mock-3.0.0, cov-2.8.1
collecting ... collected 1 item

test_pytest.py::test 
INTERNALERROR> Traceback (most recent call last):
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/_pytest/main.py", line 191, in wrap_session
INTERNALERROR>     session.exitstatus = doit(config, session) or 0
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/_pytest/main.py", line 247, in _main
INTERNALERROR>     config.hook.pytest_runtestloop(session=session)
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/hooks.py", line 286, in __call__
INTERNALERROR>     return self._hookexec(self, self.get_hookimpls(), kwargs)
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/manager.py", line 93, in _hookexec
INTERNALERROR>     return self._inner_hookexec(hook, methods, kwargs)
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/manager.py", line 84, in <lambda>
INTERNALERROR>     self._inner_hookexec = lambda hook, methods, kwargs: hook.multicall(
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/callers.py", line 208, in _multicall
INTERNALERROR>     return outcome.get_result()
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/callers.py", line 80, in get_result
INTERNALERROR>     raise ex[1].with_traceback(ex[2])
INTERNALERROR>   File "/usr/local/lib/python3.8/site-packages/pluggy/callers.py", line 187, in _multicall
INTERNALERROR>     re
[... truncated ...]

### Fix patch

```diff
diff --git a/src/_pytest/_io/saferepr.py b/src/_pytest/_io/saferepr.py
--- a/src/_pytest/_io/saferepr.py
+++ b/src/_pytest/_io/saferepr.py
@@ -20,7 +20,7 @@ def _format_repr_exception(exc: BaseException, obj: Any) -> str:
     except BaseException as exc:
         exc_info = "unpresentable exception ({})".format(_try_repr_or_str(exc))
     return "<[{} raised in repr()] {} object at 0x{:x}>".format(
-        exc_info, obj.__class__.__name__, id(obj)
+        exc_info, type(obj).__name__, id(obj)
     )
```

### Reconstructed oracle sites

- `site-0001`  src/_pytest/_io/saferepr.py:20-26
  ```
      17:         exc_info = _try_repr_or_str(exc)
      18:     except (KeyboardInterrupt, SystemExit):
      19:         raise
>>    20:     except BaseException as exc:
>>    21:         exc_info = "unpresentable exception ({})".format(_try_repr_or_str(exc))
>>    22:     return "<[{} raised in repr()] {} object at 0x{:x}>".format(
>>    23:         exc_info, obj.__class__.__name__, id(obj)
>>    24:     )
>>    25: 
>>    26: 
      27: def _ellipsize(s: str, maxsize: int) -> str:
      28:     if len(s) > maxsize:
      29:         i = max(0, (maxsize - 3) // 2)
  ```

## scikit-learn__scikit-learn-13779  (scikit-learn/scikit-learn)

### Issue (problem_statement)

Voting estimator will fail at fit if weights are passed and an estimator is None
Because we don't check for an estimator to be `None` in `sample_weight` support, `fit` is failing`.

```python
    X, y = load_iris(return_X_y=True)
    voter = VotingClassifier(
        estimators=[('lr', LogisticRegression()),
                    ('rf', RandomForestClassifier())]
    )
    voter.fit(X, y, sample_weight=np.ones(y.shape))
    voter.set_params(lr=None)
    voter.fit(X, y, sample_weight=np.ones(y.shape))
```

```
AttributeError: 'NoneType' object has no attribute 'fit'
```

### Fix patch

```diff
diff --git a/sklearn/ensemble/voting.py b/sklearn/ensemble/voting.py
--- a/sklearn/ensemble/voting.py
+++ b/sklearn/ensemble/voting.py
@@ -78,6 +78,8 @@ def fit(self, X, y, sample_weight=None):
 
         if sample_weight is not None:
             for name, step in self.estimators:
+                if step is None:
+                    continue
                 if not has_fit_parameter(step, 'sample_weight'):
                     raise ValueError('Underlying estimator \'%s\' does not'
                                      ' support sample weights.' % name)
```

### Reconstructed oracle sites

- `site-0001`  sklearn/ensemble/voting.py:78-83
  ```
      75:             raise ValueError('Number of `estimators` and weights must be equal'
      76:                              '; got %d weights, %d estimators'
      77:                              % (len(self.weights), len(self.estimators)))
>>    78: 
>>    79:         if sample_weight is not None:
>>    80:             for name, step in self.estimators:
>>    81:                 if not has_fit_parameter(step, 'sample_weight'):
>>    82:                     raise ValueError('Underlying estimator \'%s\' does not'
>>    83:                                      ' support sample weights.' % name)
      84: 
      85:         names, clfs = zip(*self.estimators)
      86:         self._validate_names(names)
  ```

## matplotlib__matplotlib-25498  (matplotlib/matplotlib)

### Issue (problem_statement)

Update colorbar after changing mappable.norm
How can I update a colorbar, after I changed the norm instance of the colorbar?

`colorbar.update_normal(mappable)` has now effect and `colorbar.update_bruteforce(mappable)` throws a `ZeroDivsionError`-Exception.

Consider this example:

``` python
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

img = 10**np.random.normal(1, 1, size=(50, 50))

fig, ax = plt.subplots(1, 1)
plot = ax.imshow(img, cmap='gray')
cb = fig.colorbar(plot, ax=ax)
plot.norm = LogNorm()
cb.update_normal(plot)  # no effect
cb.update_bruteforce(plot)  # throws ZeroDivisionError
plt.show()
```

Output for `cb.update_bruteforce(plot)`:

```
Traceback (most recent call last):
  File "test_norm.py", line 12, in <module>
    cb.update_bruteforce(plot)
  File "/home/maxnoe/.local/anaconda3/lib/python3.4/site-packages/matplotlib/colorbar.py", line 967, in update_bruteforce
    self.draw_all()
  File "/home/maxnoe/.local/anaconda3/lib/python3.4/site-packages/matplotlib/colorbar.py", line 342, in draw_all
    self._process_values()
  File "/home/maxnoe/.local/anaconda3/lib/python3.4/site-packages/matplotlib/colorbar.py", line 664, in _process_values
    b = self.norm.inverse(self._uniform_y(self.cmap.N + 1))
  File "/home/maxnoe/.local/anaconda3/lib/python3.4/site-packages/matplotlib/colors.py", line 1011, in inverse
    return vmin * ma.power((vmax / vmin), val)
ZeroDivisionError: division by zero
```

### Fix patch

```diff
diff --git a/lib/matplotlib/colorbar.py b/lib/matplotlib/colorbar.py
--- a/lib/matplotlib/colorbar.py
+++ b/lib/matplotlib/colorbar.py
@@ -301,11 +301,6 @@ def __init__(self, ax, mappable=None, *, cmap=None,
         if mappable is None:
             mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
 
-        # Ensure the given mappable's norm has appropriate vmin and vmax
-        # set even if mappable.draw has not yet been called.
-        if mappable.get_array() is not None:
-            mappable.autoscale_None()
-
         self.mappable = mappable
         cmap = mappable.cmap
         norm = mappable.norm
@@ -1101,7 +1096,10 @@ def _process_values(self):
             b = np.hstack((b, b[-1] + 1))
 
         # transform from 0-1 to vmin-vmax:
+        if self.mappable.get_array() is not None:
+            self.mappable.autoscale_None()
         if not self.norm.scaled():
+            # If we still aren't scaled after autoscaling, use 0, 1 as default
             self.norm.vmin = 0
             self.norm.vmax = 1
         self.norm.vmin, self.norm.vmax = mtransforms.nonsingular(
```

### Reconstructed oracle sites

- `site-0001`  lib/matplotlib/colorbar.py:301-311
  ```
     298:                  location=None,
     299:                  ):
     300: 
>>   301:         if mappable is None:
>>   302:             mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
>>   303: 
>>   304:         # Ensure the given mappable's norm has appropriate vmin and vmax
>>   305:         # set even if mappable.draw has not yet been called.
>>   306:         if mappable.get_array() is not None:
>>   307:             mappable.autoscale_None()
>>   308: 
>>   309:         self.mappable = mappable
>>   310:         cmap = mappable.cmap
>>   311:         norm = mappable.norm
     312: 
     313:         if isinstance(mappable, contour.ContourSet):
     314:             cs = mappable
  ```
- `site-0002`  lib/matplotlib/colorbar.py:1101-1107
  ```
    1098:         if self._extend_lower():
    1099:             b = np.hstack((b[0] - 1, b))
    1100:         if self._extend_upper():
>>  1101:             b = np.hstack((b, b[-1] + 1))
>>  1102: 
>>  1103:         # transform from 0-1 to vmin-vmax:
>>  1104:         if not self.norm.scaled():
>>  1105:             self.norm.vmin = 0
>>  1106:             self.norm.vmax = 1
>>  1107:         self.norm.vmin, self.norm.vmax = mtransforms.nonsingular(
    1108:             self.norm.vmin, self.norm.vmax, expander=0.1)
    1109:         if (not isinstance(self.norm, colors.BoundaryNorm) and
    1110:                 (self.boundaries is None)):
  ```

## sphinx-doc__sphinx-8474  (sphinx-doc/sphinx)

### Issue (problem_statement)

v3.3 upgrade started generating "WARNING: no number is assigned for table" warnings
We've updated to Sphinx 3.3 in our documentation, and suddenly the following warning started popping up in our builds when we build either `singlehtml` or `latex`.:

`WARNING: no number is assigned for table:`

I looked through the changelog but it didn't seem like there was anything related to `numref` that was changed, but perhaps I missed something? Could anyone point me to a change in the numref logic so I can figure out where these warnings are coming from?

### Fix patch

```diff
diff --git a/sphinx/domains/std.py b/sphinx/domains/std.py
--- a/sphinx/domains/std.py
+++ b/sphinx/domains/std.py
@@ -852,8 +852,9 @@ def _resolve_numref_xref(self, env: "BuildEnvironment", fromdocname: str,
             if fignumber is None:
                 return contnode
         except ValueError:
-            logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
-                           location=node)
+            logger.warning(__("Failed to create a cross reference. Any number is not "
+                              "assigned: %s"),
+                           labelid, location=node)
             return contnode
 
         try:
```

### Reconstructed oracle sites

- `site-0001`  sphinx/domains/std.py:852-859
  ```
     849: 
     850:         try:
     851:             fignumber = self.get_fignumber(env, builder, figtype, docname, target_node)
>>   852:             if fignumber is None:
>>   853:                 return contnode
>>   854:         except ValueError:
>>   855:             logger.warning(__("no number is assigned for %s: %s"), figtype, labelid,
>>   856:                            location=node)
>>   857:             return contnode
>>   858: 
>>   859:         try:
     860:             if node['refexplicit']:
     861:                 title = contnode.astext()
     862:             else:
  ```

## pylint-dev__pylint-6506  (pylint-dev/pylint)

### Issue (problem_statement)

Traceback printed for unrecognized option
### Bug description

A traceback is printed when an unrecognized option is passed to pylint.

### Configuration

_No response_

### Command used

```shell
pylint -Q
```


### Pylint output

```shell
************* Module Command line
Command line:1:0: E0015: Unrecognized option found: Q (unrecognized-option)
Traceback (most recent call last):
  File "/Users/markbyrne/venv310/bin/pylint", line 33, in <module>
    sys.exit(load_entry_point('pylint', 'console_scripts', 'pylint')())
  File "/Users/markbyrne/programming/pylint/pylint/__init__.py", line 24, in run_pylint
    PylintRun(argv or sys.argv[1:])
  File "/Users/markbyrne/programming/pylint/pylint/lint/run.py", line 135, in __init__
    args = _config_initialization(
  File "/Users/markbyrne/programming/pylint/pylint/config/config_initialization.py", line 85, in _config_initialization
    raise _UnrecognizedOptionError(options=unrecognized_options)
pylint.config.exceptions._UnrecognizedOptionError
```


### Expected behavior

The top part of the current output is handy:
`Command line:1:0: E0015: Unrecognized option found: Q (unrecognized-option)`

The traceback I don't think is expected & not user-friendly.
A usage tip, for example:
```python
mypy -Q
usage: mypy [-h] [-v] [-V] [more options; see below]
            [-m MODULE] [-p PACKAGE] [-c PROGRAM_TEXT] [files ...]
mypy: error: unrecognized arguments: -Q
```

### Pylint version

```shell
pylint 2.14.0-dev0
astroid 2.11.3
Python 3.10.0b2 (v3.10.0b2:317314165a, May 31 2021, 10:02:22) [Clang 12.0.5 (clang-1205.0.22.9)]
```


### OS / Environment

_No response_

### Additional dependencies

_No response_

### Fix patch

```diff
diff --git a/pylint/config/config_initialization.py b/pylint/config/config_initialization.py
--- a/pylint/config/config_initialization.py
+++ b/pylint/config/config_initialization.py
@@ -81,8 +81,7 @@ def _config_initialization(
             unrecognized_options.append(opt[1:])
     if unrecognized_options:
         msg = ", ".join(unrecognized_options)
-        linter.add_message("unrecognized-option", line=0, args=msg)
-        raise _UnrecognizedOptionError(options=unrecognized_options)
+        linter._arg_parser.error(f"Unrecognized option found: {msg}")
 
     # Set the current module to configuration as we don't know where
     # the --load-plugins key is coming from
```

### Reconstructed oracle sites

- `site-0001`  pylint/config/config_initialization.py:81-88
  ```
      78:         if opt.startswith("--"):
      79:             unrecognized_options.append(opt[2:])
      80:         elif opt.startswith("-"):
>>    81:             unrecognized_options.append(opt[1:])
>>    82:     if unrecognized_options:
>>    83:         msg = ", ".join(unrecognized_options)
>>    84:         linter.add_message("unrecognized-option", line=0, args=msg)
>>    85:         raise _UnrecognizedOptionError(options=unrecognized_options)
>>    86: 
>>    87:     # Set the current module to configuration as we don't know where
>>    88:     # the --load-plugins key is coming from
      89:     linter.set_current_module("Command line or configuration file")
      90: 
      91:     # We have loaded configuration from config file and command line. Now, we can
  ```

## psf__requests-1963  (psf/requests)

### Issue (problem_statement)

`Session.resolve_redirects` copies the original request for all subsequent requests, can cause incorrect method selection
Consider the following redirection chain:

```
POST /do_something HTTP/1.1
Host: server.example.com
...

HTTP/1.1 303 See Other
Location: /new_thing_1513

GET /new_thing_1513
Host: server.example.com
...

HTTP/1.1 307 Temporary Redirect
Location: //failover.example.com/new_thing_1513
```

The intermediate 303 See Other has caused the POST to be converted to
a GET.  The subsequent 307 should preserve the GET.  However, because
`Session.resolve_redirects` starts each iteration by copying the _original_
request object, Requests will issue a POST!

### Fix patch

```diff
diff --git a/requests/sessions.py b/requests/sessions.py
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -168,8 +168,11 @@ def resolve_redirects(self, resp, req, stream=False, timeout=None,
             if new_auth is not None:
                 prepared_request.prepare_auth(new_auth)
 
+            # Override the original request.
+            req = prepared_request
+
             resp = self.send(
-                prepared_request,
+                req,
                 stream=stream,
                 timeout=timeout,
                 verify=verify,
```

### Reconstructed oracle sites

- `site-0001`  requests/sessions.py:168-175
  ```
     165: 
     166:             # .netrc might have more auth for us.
     167:             new_auth = get_netrc_auth(url) if self.trust_env else None
>>   168:             if new_auth is not None:
>>   169:                 prepared_request.prepare_auth(new_auth)
>>   170: 
>>   171:             resp = self.send(
>>   172:                 prepared_request,
>>   173:                 stream=stream,
>>   174:                 timeout=timeout,
>>   175:                 verify=verify,
     176:                 cert=cert,
     177:                 proxies=proxies,
     178:                 allow_redirects=False,
  ```

## django__django-12908  (django/django)

### Issue (problem_statement)

Union queryset should raise on distinct().
Description
	 
		(last modified by Sielc Technologies)
	 
After using
.annotate() on 2 different querysets
and then .union()
.distinct() will not affect the queryset
	def setUp(self) -> None:
		user = self.get_or_create_admin_user()
		Sample.h.create(user, name="Sam1")
		Sample.h.create(user, name="Sam2 acid")
		Sample.h.create(user, name="Sam3")
		Sample.h.create(user, name="Sam4 acid")
		Sample.h.create(user, name="Dub")
		Sample.h.create(user, name="Dub")
		Sample.h.create(user, name="Dub")
		self.user = user
	def test_union_annotated_diff_distinct(self):
		qs = Sample.objects.filter(user=self.user)
		qs1 = qs.filter(name='Dub').annotate(rank=Value(0, IntegerField()))
		qs2 = qs.filter(name='Sam1').annotate(rank=Value(1, IntegerField()))
		qs = qs1.union(qs2)
		qs = qs.order_by('name').distinct('name') # THIS DISTINCT DOESN'T WORK
		self.assertEqual(qs.count(), 2)
expected to get wrapped union
	SELECT DISTINCT ON (siebox_sample.name) * FROM (SELECT ... UNION SELECT ...) AS siebox_sample

### Fix patch

```diff
diff --git a/django/db/models/query.py b/django/db/models/query.py
--- a/django/db/models/query.py
+++ b/django/db/models/query.py
@@ -1138,6 +1138,7 @@ def distinct(self, *field_names):
         """
         Return a new QuerySet instance that will select only distinct results.
         """
+        self._not_support_combined_queries('distinct')
         assert not self.query.is_sliced, \
             "Cannot create distinct fields once a slice has been taken."
         obj = self._chain()
```

### Reconstructed oracle sites

- `site-0001`  django/db/models/query.py:1138-1143
  ```
    1135:         return obj
    1136: 
    1137:     def distinct(self, *field_names):
>>  1138:         """
>>  1139:         Return a new QuerySet instance that will select only distinct results.
>>  1140:         """
>>  1141:         assert not self.query.is_sliced, \
>>  1142:             "Cannot create distinct fields once a slice has been taken."
>>  1143:         obj = self._chain()
    1144:         obj.query.add_distinct_fields(*field_names)
    1145:         return obj
    1146: 
  ```

## sympy__sympy-19254  (sympy/sympy)

### Issue (problem_statement)

sympy.polys.factortools.dmp_zz_mignotte_bound improvement
The method `dup_zz_mignotte_bound(f, K)` can be significantly improved by using the **Knuth-Cohen bound** instead. After our research with Prof. Ag.Akritas we have implemented the Knuth-Cohen bound among others, and compare them among dozens of polynomials with different degree, density and coefficients range. Considering the results and the feedback from Mr.Kalevi Suominen, our proposal is that the mignotte_bound should be replaced by the knuth-cohen bound.
Also, `dmp_zz_mignotte_bound(f, u, K)` for mutli-variants polynomials should be replaced appropriately.

### Fix patch

```diff
diff --git a/sympy/polys/factortools.py b/sympy/polys/factortools.py
--- a/sympy/polys/factortools.py
+++ b/sympy/polys/factortools.py
@@ -124,13 +124,64 @@ def dmp_trial_division(f, factors, u, K):
 
 
 def dup_zz_mignotte_bound(f, K):
-    """Mignotte bound for univariate polynomials in `K[x]`. """
-    a = dup_max_norm(f, K)
-    b = abs(dup_LC(f, K))
-    n = dup_degree(f)
+    """
+    The Knuth-Cohen variant of Mignotte bound for
+    univariate polynomials in `K[x]`.
 
-    return K.sqrt(K(n + 1))*2**n*a*b
+    Examples
+    ========
+
+    >>> from sympy.polys import ring, ZZ
+    >>> R, x = ring("x", ZZ)
+
+    >>> f = x**3 + 14*x**2 + 56*x + 64
+    >>> R.dup_zz_mignotte_bound(f)
+    152
+
+    By checking `factor(f)` we can see that max coeff is 8
+
+    Also consider a case that `f` is irreducible for example `f = 2*x**2 + 3*x + 4`
+    To avoid a bug for these cases, we return the bound plus the max coefficient of `f`
+
+    >>> f = 2*x**2 + 3*x + 4
+    >>> R.dup_zz_mignotte_bound(f)
+    6
+
+    Lastly,To see the difference between the new and the old Mignotte bound
+    consider the irreducible polynomial::
+
+    >>> f = 87*x**7 + 4*x**6 + 80*x**5 + 17*x**4 + 9*x**3 + 12*x**2 + 49*x + 26
+    >>> R.dup_zz_mignotte_bound(f)
+    744
+
+    The new Mignotte bound is 744 whereas the old one (SymPy 1.5.1) is 1937664.
+
+
+    References
+    ==========
+
+    ..[1] [Abbott2013]_
+
+    """
+    from sympy import binomial
+
+    d = dup_degree(f)
+    delta = _ceil(d / 2)
+    delta2 = _ceil(delta / 2)
+
+    # euclidean-norm
+    eucl_norm = K.sqrt( sum( [cf**2 for cf in f] ) )
+
+    # biggest values of binomial coefficients (p. 538 of reference)
+    t1 = binomial(delta - 1, delta2)
+    t2 = binomial(delta - 1, delta2 - 1)
+
+    lc = K.abs(dup_LC(f, K))   # leading coefficient
+    bound = t1 * eucl_norm + t2 * lc   # (p. 538 of reference)
+    bound += dup_max_norm(f, K) # add max coeff for irreducible polys
+    bound = _ceil(bound / 2) * 2   # round up to even integer
 
+    return bound
 
 def dmp_zz_mignotte_bound(f, u, K):
     """Mignotte bound for multivariate polynomials in `K[X]`. """
```

### Reconstructed oracle sites

- `site-0001`  sympy/polys/factortools.py:124-136
  ```
     121:         result.append((factor, k))
     122: 
     123:     return _sort_factors(result)
>>   124: 
>>   125: 
>>   126: def dup_zz_mignotte_bound(f, K):
>>   127:     """Mignotte bound for univariate polynomials in `K[x]`. """
>>   128:     a = dup_max_norm(f, K)
>>   129:     b = abs(dup_LC(f, K))
>>   130:     n = dup_degree(f)
>>   131: 
>>   132:     return K.sqrt(K(n + 1))*2**n*a*b
>>   133: 
>>   134: 
>>   135: def dmp_zz_mignotte_bound(f, u, K):
>>   136:     """Mignotte bound for multivariate polynomials in `K[X]`. """
     137:     a = dmp_max_norm(f, u, K)
     138:     b = abs(dmp_ground_LC(f, u, K))
     139:     n = sum(dmp_degree_list(f, u))
  ```

## pytest-dev__pytest-5227  (pytest-dev/pytest)

### Issue (problem_statement)

Improve default logging format
Currently it is:

> DEFAULT_LOG_FORMAT = "%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s"

I think `name` (module name) would be very useful here, instead of just the base filename.

(It might also be good to have the relative path there (maybe at the end), but it is usually still very long (but e.g. `$VIRTUAL_ENV` could be substituted therein))

Currently it would look like this:
```
utils.py                   114 DEBUG    (0.000) SELECT "app_url"."id", "app_url"."created", "app_url"."url" FROM "app_url" WHERE "app_url"."id" = 2; args=(2,)
multipart.py               604 DEBUG    Calling on_field_start with no data
```


Using `DEFAULT_LOG_FORMAT = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"` instead:

```
DEBUG    django.db.backends:utils.py:114 (0.000) SELECT "app_url"."id", "app_url"."created", "app_url"."url" FROM "app_url" WHERE "app_url"."id" = 2; args=(2,)
DEBUG    multipart.multipart:multipart.py:604 Calling on_field_start with no data
```

### Fix patch

```diff
diff --git a/src/_pytest/logging.py b/src/_pytest/logging.py
--- a/src/_pytest/logging.py
+++ b/src/_pytest/logging.py
@@ -15,7 +15,7 @@
 from _pytest.config import create_terminal_writer
 from _pytest.pathlib import Path
 
-DEFAULT_LOG_FORMAT = "%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s"
+DEFAULT_LOG_FORMAT = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"
 DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"
```

### Reconstructed oracle sites

- `site-0001`  src/_pytest/logging.py:15-21
  ```
      12: 
      13: import pytest
      14: from _pytest.compat import dummy_context_manager
>>    15: from _pytest.config import create_terminal_writer
>>    16: from _pytest.pathlib import Path
>>    17: 
>>    18: DEFAULT_LOG_FORMAT = "%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s"
>>    19: DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"
>>    20: 
>>    21: 
      22: class ColoredLevelFormatter(logging.Formatter):
      23:     """
      24:     Colorize the %(levelname)..s part of the log format passed to __init__.
  ```

## scikit-learn__scikit-learn-13496  (scikit-learn/scikit-learn)

### Issue (problem_statement)

Expose warm_start in Isolation forest
It seems to me that `sklearn.ensemble.IsolationForest` supports incremental addition of new trees with the `warm_start` parameter of its parent class, `sklearn.ensemble.BaseBagging`.

Even though this parameter is not exposed in `__init__()` , it gets inherited from `BaseBagging` and one can use it by changing it to `True` after initialization. To make it work, you have to also increment `n_estimators` on every iteration. 

It took me a while to notice that it actually works, and I had to inspect the source code of both `IsolationForest` and `BaseBagging`. Also, it looks to me that the behavior is in-line with `sklearn.ensemble.BaseForest` that is behind e.g. `sklearn.ensemble.RandomForestClassifier`.

To make it more easier to use, I'd suggest to:
* expose `warm_start` in `IsolationForest.__init__()`, default `False`;
* document it in the same way as it is documented for `RandomForestClassifier`, i.e. say:
```py
    warm_start : bool, optional (default=False)
        When set to ``True``, reuse the solution of the previous call to fit
        and add more estimators to the ensemble, otherwise, just fit a whole
        new forest. See :term:`the Glossary <warm_start>`.
```
* add a test to make sure it works properly;
* possibly also mention in the "IsolationForest example" documentation entry;

### Fix patch

```diff
diff --git a/sklearn/ensemble/iforest.py b/sklearn/ensemble/iforest.py
--- a/sklearn/ensemble/iforest.py
+++ b/sklearn/ensemble/iforest.py
@@ -120,6 +120,12 @@ class IsolationForest(BaseBagging, OutlierMixin):
     verbose : int, optional (default=0)
         Controls the verbosity of the tree building process.
 
+    warm_start : bool, optional (default=False)
+        When set to ``True``, reuse the solution of the previous call to fit
+        and add more estimators to the ensemble, otherwise, just fit a whole
+        new forest. See :term:`the Glossary <warm_start>`.
+
+        .. versionadded:: 0.21
 
     Attributes
     ----------
@@ -173,7 +179,8 @@ def __init__(self,
                  n_jobs=None,
                  behaviour='old',
                  random_state=None,
-                 verbose=0):
+                 verbose=0,
+                 warm_start=False):
         super().__init__(
             base_estimator=ExtraTreeRegressor(
                 max_features=1,
@@ -185,6 +192,7 @@ def __init__(self,
             n_estimators=n_estimators,
             max_samples=max_samples,
             max_features=max_features,
+            warm_start=warm_start,
             n_jobs=n_jobs,
             random_state=random_state,
             verbose=verbose)
```

### Reconstructed oracle sites

- `site-0001`  sklearn/ensemble/iforest.py:120-125
  ```
     117:         If None, the random number generator is the RandomState instance used
     118:         by `np.random`.
     119: 
>>   120:     verbose : int, optional (default=0)
>>   121:         Controls the verbosity of the tree building process.
>>   122: 
>>   123: 
>>   124:     Attributes
>>   125:     ----------
     126:     estimators_ : list of DecisionTreeClassifier
     127:         The collection of fitted sub-estimators.
     128: 
  ```
- `site-0002`  sklearn/ensemble/iforest.py:173-179
  ```
     170:                  contamination="legacy",
     171:                  max_features=1.,
     172:                  bootstrap=False,
>>   173:                  n_jobs=None,
>>   174:                  behaviour='old',
>>   175:                  random_state=None,
>>   176:                  verbose=0):
>>   177:         super().__init__(
>>   178:             base_estimator=ExtraTreeRegressor(
>>   179:                 max_features=1,
     180:                 splitter='random',
     181:                 random_state=random_state),
     182:             # here above max_features has no links with self.max_features
  ```
- `site-0003`  sklearn/ensemble/iforest.py:185-190
  ```
     182:             # here above max_features has no links with self.max_features
     183:             bootstrap=bootstrap,
     184:             bootstrap_features=False,
>>   185:             n_estimators=n_estimators,
>>   186:             max_samples=max_samples,
>>   187:             max_features=max_features,
>>   188:             n_jobs=n_jobs,
>>   189:             random_state=random_state,
>>   190:             verbose=verbose)
     191: 
     192:         self.behaviour = behaviour
     193:         self.contamination = contamination
  ```

## matplotlib__matplotlib-26020  (matplotlib/matplotlib)

### Issue (problem_statement)

Error creating AxisGrid with non-default axis class
<!--To help us understand and resolve your issue, please fill out the form to the best of your ability.-->
<!--You can feel free to delete the sections that do not apply.-->

### Bug report

**Bug summary**

Creating `AxesGrid` using cartopy `GeoAxes` as `axis_class` raises `TypeError: 'method' object is not subscriptable`. Seems to be due to different behaviour of `axis` attr. for `mpl_toolkits.axes_grid1.mpl_axes.Axes` and other axes instances (like `GeoAxes`) where `axis` is only a callable. The error is raised in method `mpl_toolkits.axes_grid1.axes_grid._tick_only` when trying to access keys from `axis` attr.

**Code for reproduction**

<!--A minimum code snippet required to reproduce the bug.
Please make sure to minimize the number of dependencies required, and provide
any necessary plotted data.
Avoid using threads, as Matplotlib is (explicitly) not thread-safe.-->

```python
import matplotlib.pyplot as plt
from cartopy.crs import PlateCarree
from cartopy.mpl.geoaxes import GeoAxes
from mpl_toolkits.axes_grid1 import AxesGrid

fig = plt.figure()
axes_class = (GeoAxes, dict(map_projection=PlateCarree()))
gr = AxesGrid(fig, 111, nrows_ncols=(1,1),
              axes_class=axes_class)
```

**Actual outcome**

<!--The output produced by the above code, which may be a screenshot, console output, etc.-->

```
Traceback (most recent call last):

  File "/home/jonasg/stuff/bugreport_mpl_toolkits_AxesGrid.py", line 16, in <module>
    axes_class=axes_class)

  File "/home/jonasg/miniconda3/envs/pya/lib/python3.7/site-packages/mpl_toolkits/axes_grid1/axes_grid.py", line 618, in __init__
    self.set_label_mode(label_mode)

  File "/home/jonasg/miniconda3/envs/pya/lib/python3.7/site-packages/mpl_toolkits/axes_grid1/axes_grid.py", line 389, in set_label_mode
    _tick_only(ax, bottom_on=False, left_on=False)

  File "/home/jonasg/miniconda3/envs/pya/lib/python3.7/site-packages
[... truncated ...]

### Fix patch

```diff
diff --git a/lib/mpl_toolkits/axes_grid1/axes_grid.py b/lib/mpl_toolkits/axes_grid1/axes_grid.py
--- a/lib/mpl_toolkits/axes_grid1/axes_grid.py
+++ b/lib/mpl_toolkits/axes_grid1/axes_grid.py
@@ -1,5 +1,6 @@
 from numbers import Number
 import functools
+from types import MethodType
 
 import numpy as np
 
@@ -7,14 +8,20 @@
 from matplotlib.gridspec import SubplotSpec
 
 from .axes_divider import Size, SubplotDivider, Divider
-from .mpl_axes import Axes
+from .mpl_axes import Axes, SimpleAxisArtist
 
 
 def _tick_only(ax, bottom_on, left_on):
     bottom_off = not bottom_on
     left_off = not left_on
-    ax.axis["bottom"].toggle(ticklabels=bottom_off, label=bottom_off)
-    ax.axis["left"].toggle(ticklabels=left_off, label=left_off)
+    if isinstance(ax.axis, MethodType):
+        bottom = SimpleAxisArtist(ax.xaxis, 1, ax.spines["bottom"])
+        left = SimpleAxisArtist(ax.yaxis, 1, ax.spines["left"])
+    else:
+        bottom = ax.axis["bottom"]
+        left = ax.axis["left"]
+    bottom.toggle(ticklabels=bottom_off, label=bottom_off)
+    left.toggle(ticklabels=left_off, label=left_off)
 
 
 class CbarAxesBase:
```

### Reconstructed oracle sites

- `site-0001`  lib/mpl_toolkits/axes_grid1/axes_grid.py:1-5
  ```
>>     1: from numbers import Number
>>     2: import functools
>>     3: 
>>     4: import numpy as np
>>     5: 
       6: from matplotlib import _api, cbook
       7: from matplotlib.gridspec import SubplotSpec
       8: 
  ```
- `site-0002`  lib/mpl_toolkits/axes_grid1/axes_grid.py:7-20
  ```
       4: import numpy as np
       5: 
       6: from matplotlib import _api, cbook
>>     7: from matplotlib.gridspec import SubplotSpec
>>     8: 
>>     9: from .axes_divider import Size, SubplotDivider, Divider
>>    10: from .mpl_axes import Axes
>>    11: 
>>    12: 
>>    13: def _tick_only(ax, bottom_on, left_on):
>>    14:     bottom_off = not bottom_on
>>    15:     left_off = not left_on
>>    16:     ax.axis["bottom"].toggle(ticklabels=bottom_off, label=bottom_off)
>>    17:     ax.axis["left"].toggle(ticklabels=left_off, label=left_off)
>>    18: 
>>    19: 
>>    20: class CbarAxesBase:
      21:     def __init__(self, *args, orientation, **kwargs):
      22:         self.orientation = orientation
      23:         super().__init__(*args, **kwargs)
  ```

## sphinx-doc__sphinx-8282  (sphinx-doc/sphinx)

### Issue (problem_statement)

autodoc_typehints does not effect to overloaded callables
**Describe the bug**
autodoc_typehints does not effect to overloaded callables.

**To Reproduce**

```
# in conf.py
autodoc_typehints = 'none'
```
```
# in index.rst
.. automodule:: example
   :members:
   :undoc-members:
```
```
# in example.py
from typing import overload


@overload
def foo(x: int) -> int:
    ...


@overload
def foo(x: float) -> float:
    ...


def foo(x):
    return x
```

**Expected behavior**
All typehints for overloaded callables are obeyed `autodoc_typehints` setting.

**Your project**
No

**Screenshots**
No

**Environment info**
- OS: Mac
- Python version: 3.8.2
- Sphinx version: 3.1.0dev
- Sphinx extensions: sphinx.ext.autodoc
- Extra tools: No

**Additional context**
No

### Fix patch

```diff
diff --git a/sphinx/ext/autodoc/__init__.py b/sphinx/ext/autodoc/__init__.py
--- a/sphinx/ext/autodoc/__init__.py
+++ b/sphinx/ext/autodoc/__init__.py
@@ -1240,7 +1240,9 @@ def add_directive_header(self, sig: str) -> None:
 
     def format_signature(self, **kwargs: Any) -> str:
         sigs = []
-        if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
+        if (self.analyzer and
+                '.'.join(self.objpath) in self.analyzer.overloads and
+                self.env.config.autodoc_typehints == 'signature'):
             # Use signatures for overloaded functions instead of the implementation function.
             overloaded = True
         else:
@@ -1474,7 +1476,7 @@ def format_signature(self, **kwargs: Any) -> str:
         sigs = []
 
         overloads = self.get_overloaded_signatures()
-        if overloads:
+        if overloads and self.env.config.autodoc_typehints == 'signature':
             # Use signatures for overloaded methods instead of the implementation method.
             method = safe_getattr(self._signature_class, self._signature_method_name, None)
             __globals__ = safe_getattr(method, '__globals__', {})
@@ -1882,7 +1884,9 @@ def document_members(self, all_members: bool = False) -> None:
 
     def format_signature(self, **kwargs: Any) -> str:
         sigs = []
-        if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
+        if (self.analyzer and
+                '.'.join(self.objpath) in self.analyzer.overloads and
+                self.env.config.autodoc_typehints == 'signature'):
             # Use signatures for overloaded methods instead of the implementation method.
             overloaded = True
         else:
```

### Reconstructed oracle sites

- `site-0001`  sphinx/ext/autodoc/__init__.py:1240-1246
  ```
    1237: 
    1238:         if inspect.iscoroutinefunction(self.object):
    1239:             self.add_line('   :async:', sourcename)
>>  1240: 
>>  1241:     def format_signature(self, **kwargs: Any) -> str:
>>  1242:         sigs = []
>>  1243:         if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
>>  1244:             # Use signatures for overloaded functions instead of the implementation function.
>>  1245:             overloaded = True
>>  1246:         else:
    1247:             overloaded = False
    1248:             sig = super().format_signature(**kwargs)
    1249:             sigs.append(sig)
  ```
- `site-0002`  sphinx/ext/autodoc/__init__.py:1474-1480
  ```
    1471:             return ''
    1472: 
    1473:         sig = super().format_signature()
>>  1474:         sigs = []
>>  1475: 
>>  1476:         overloads = self.get_overloaded_signatures()
>>  1477:         if overloads:
>>  1478:             # Use signatures for overloaded methods instead of the implementation method.
>>  1479:             method = safe_getattr(self._signature_class, self._signature_method_name, None)
>>  1480:             __globals__ = safe_getattr(method, '__globals__', {})
    1481:             for overload in overloads:
    1482:                 overload = evaluate_signature(overload, __globals__,
    1483:                                               self.env.config.autodoc_type_aliases)
  ```
- `site-0003`  sphinx/ext/autodoc/__init__.py:1882-1888
  ```
    1879: 
    1880:     def document_members(self, all_members: bool = False) -> None:
    1881:         pass
>>  1882: 
>>  1883:     def format_signature(self, **kwargs: Any) -> str:
>>  1884:         sigs = []
>>  1885:         if self.analyzer and '.'.join(self.objpath) in self.analyzer.overloads:
>>  1886:             # Use signatures for overloaded methods instead of the implementation method.
>>  1887:             overloaded = True
>>  1888:         else:
    1889:             overloaded = False
    1890:             sig = super().format_signature(**kwargs)
    1891:             sigs.append(sig)
  ```

## pylint-dev__pylint-7228  (pylint-dev/pylint)

### Issue (problem_statement)

rxg include '\p{Han}' will throw error
### Bug description

config rxg in pylintrc with \p{Han} will throw err

### Configuration
.pylintrc:

```ini
function-rgx=[\p{Han}a-z_][\p{Han}a-z0-9_]{2,30}$
```

### Command used

```shell
pylint
```


### Pylint output

```shell
(venvtest) tsung-hande-MacBook-Pro:robot_is_comming tsung-han$ pylint
Traceback (most recent call last):
  File "/Users/tsung-han/PycharmProjects/robot_is_comming/venvtest/bin/pylint", line 8, in <module>
    sys.exit(run_pylint())
  File "/Users/tsung-han/PycharmProjects/robot_is_comming/venvtest/lib/python3.9/site-packages/pylint/__init__.py", line 25, in run_pylint
    PylintRun(argv or sys.argv[1:])
  File "/Users/tsung-han/PycharmProjects/robot_is_comming/venvtest/lib/python3.9/site-packages/pylint/lint/run.py", line 161, in __init__
    args = _config_initialization(
  File "/Users/tsung-han/PycharmProjects/robot_is_comming/venvtest/lib/python3.9/site-packages/pylint/config/config_initialization.py", line 57, in _config_initialization
    linter._parse_configuration_file(config_args)
  File "/Users/tsung-han/PycharmProjects/robot_is_comming/venvtest/lib/python3.9/site-packages/pylint/config/arguments_manager.py", line 244, in _parse_configuration_file
    self.config, parsed_args = self._arg_parser.parse_known_args(
  File "/usr/local/Cellar/python@3.9/3.9.13_1/Frameworks/Python.framework/Versions/3.9/lib/python3.9/argparse.py", line 1858, in parse_known_args
    namespace, args = self._parse_known_args(args, namespace)
  File "/usr/local/Cellar/python@3.9/3.9.13_1/Frameworks/Python.framework/Versions/3.9/lib/python3.9/argparse.py", line 2067, in _parse_known_args
    start_index = consume_optional(start_index)
  File "/usr/local/Cellar/python@3.9/3.9.13_1/Frameworks/Python.framework/Versions/3.9/lib/python3.9/argparse.py", line 2007, in consume_optional
    take_action(action, args, option_string)
  File "/usr/local/Cellar/python@3.9/3.9.13_1/Frameworks/
[... truncated ...]

### Fix patch

```diff
diff --git a/pylint/config/argument.py b/pylint/config/argument.py
--- a/pylint/config/argument.py
+++ b/pylint/config/argument.py
@@ -99,11 +99,20 @@ def _py_version_transformer(value: str) -> tuple[int, ...]:
     return version
 
 
+def _regex_transformer(value: str) -> Pattern[str]:
+    """Return `re.compile(value)`."""
+    try:
+        return re.compile(value)
+    except re.error as e:
+        msg = f"Error in provided regular expression: {value} beginning at index {e.pos}: {e.msg}"
+        raise argparse.ArgumentTypeError(msg)
+
+
 def _regexp_csv_transfomer(value: str) -> Sequence[Pattern[str]]:
     """Transforms a comma separated list of regular expressions."""
     patterns: list[Pattern[str]] = []
     for pattern in _csv_transformer(value):
-        patterns.append(re.compile(pattern))
+        patterns.append(_regex_transformer(pattern))
     return patterns
 
 
@@ -130,7 +139,7 @@ def _regexp_paths_csv_transfomer(value: str) -> Sequence[Pattern[str]]:
     "non_empty_string": _non_empty_string_transformer,
     "path": _path_transformer,
     "py_version": _py_version_transformer,
-    "regexp": re.compile,
+    "regexp": _regex_transformer,
     "regexp_csv": _regexp_csv_transfomer,
     "regexp_paths_csv": _regexp_paths_csv_transfomer,
     "string": pylint_utils._unquote,
```

### Reconstructed oracle sites

- `site-0001`  pylint/config/argument.py:99-109
  ```
      96:         raise argparse.ArgumentTypeError(
      97:             f"{value} has an invalid format, should be a version string. E.g., '3.8'"
      98:         ) from None
>>    99:     return version
>>   100: 
>>   101: 
>>   102: def _regexp_csv_transfomer(value: str) -> Sequence[Pattern[str]]:
>>   103:     """Transforms a comma separated list of regular expressions."""
>>   104:     patterns: list[Pattern[str]] = []
>>   105:     for pattern in _csv_transformer(value):
>>   106:         patterns.append(re.compile(pattern))
>>   107:     return patterns
>>   108: 
>>   109: 
     110: def _regexp_paths_csv_transfomer(value: str) -> Sequence[Pattern[str]]:
     111:     """Transforms a comma separated list of regular expressions paths."""
     112:     patterns: list[Pattern[str]] = []
  ```
- `site-0002`  pylint/config/argument.py:130-136
  ```
     127:     "float": float,
     128:     "int": int,
     129:     "confidence": _confidence_transformer,
>>   130:     "non_empty_string": _non_empty_string_transformer,
>>   131:     "path": _path_transformer,
>>   132:     "py_version": _py_version_transformer,
>>   133:     "regexp": re.compile,
>>   134:     "regexp_csv": _regexp_csv_transfomer,
>>   135:     "regexp_paths_csv": _regexp_paths_csv_transfomer,
>>   136:     "string": pylint_utils._unquote,
     137:     "yn": _yn_transformer,
     138: }
     139: """Type transformers for all argument types.
  ```

## django__django-12915  (django/django)

### Issue (problem_statement)

Add get_response_async for ASGIStaticFilesHandler
Description
	
It looks like the StaticFilesHandlerMixin is missing the the async response function.
Without this, when trying to use the ASGIStaticFilesHandler, this is the traceback:
Exception inside application: 'NoneType' object is not callable
Traceback (most recent call last):
 File ".../lib/python3.7/site-packages/daphne/cli.py", line 30, in asgi
	await self.app(scope, receive, send)
 File ".../src/django/django/contrib/staticfiles/handlers.py", line 86, in __call__
	return await super().__call__(scope, receive, send)
 File ".../src/django/django/core/handlers/asgi.py", line 161, in __call__
	response = await self.get_response_async(request)
 File ".../src/django/django/core/handlers/base.py", line 148, in get_response_async
	response = await self._middleware_chain(request)
TypeError: 'NoneType' object is not callable

### Fix patch

```diff
diff --git a/django/contrib/staticfiles/handlers.py b/django/contrib/staticfiles/handlers.py
--- a/django/contrib/staticfiles/handlers.py
+++ b/django/contrib/staticfiles/handlers.py
@@ -1,6 +1,8 @@
 from urllib.parse import urlparse
 from urllib.request import url2pathname
 
+from asgiref.sync import sync_to_async
+
 from django.conf import settings
 from django.contrib.staticfiles import utils
 from django.contrib.staticfiles.views import serve
@@ -52,6 +54,12 @@ def get_response(self, request):
         except Http404 as e:
             return response_for_exception(request, e)
 
+    async def get_response_async(self, request):
+        try:
+            return await sync_to_async(self.serve)(request)
+        except Http404 as e:
+            return await sync_to_async(response_for_exception)(request, e)
+
 
 class StaticFilesHandler(StaticFilesHandlerMixin, WSGIHandler):
     """
```

### Reconstructed oracle sites

- `site-0001`  django/contrib/staticfiles/handlers.py:1-6
  ```
>>     1: from urllib.parse import urlparse
>>     2: from urllib.request import url2pathname
>>     3: 
>>     4: from django.conf import settings
>>     5: from django.contrib.staticfiles import utils
>>     6: from django.contrib.staticfiles.views import serve
       7: from django.core.handlers.asgi import ASGIHandler
       8: from django.core.handlers.exception import response_for_exception
       9: from django.core.handlers.wsgi import WSGIHandler, get_path_info
  ```
- `site-0002`  django/contrib/staticfiles/handlers.py:52-57
  ```
      49:     def get_response(self, request):
      50:         try:
      51:             return self.serve(request)
>>    52:         except Http404 as e:
>>    53:             return response_for_exception(request, e)
>>    54: 
>>    55: 
>>    56: class StaticFilesHandler(StaticFilesHandlerMixin, WSGIHandler):
>>    57:     """
      58:     WSGI middleware that intercepts calls to the static files directory, as
      59:     defined by the STATIC_URL setting, and serves those files.
      60:     """
  ```

## sympy__sympy-20212  (sympy/sympy)

### Issue (problem_statement)

0**-oo produces 0, the documentation says it should produce zoo
Using SymPy 1.5.1, evaluate `0**-oo` produces `0`.

The documentation for the Pow class states that it should return `ComplexInfinity`, aka `zoo`

| expr | value | reason |
| :-- | :-- | :--|
| `0**-oo` | `zoo` | This is not strictly true, as 0**oo may be oscillating between positive and negative values or rotating in the complex plane. It is convenient, however, when the base is positive.|

### Fix patch

```diff
diff --git a/sympy/core/power.py b/sympy/core/power.py
--- a/sympy/core/power.py
+++ b/sympy/core/power.py
@@ -291,6 +291,8 @@ def __new__(cls, b, e, evaluate=None):
             ).warn()
 
         if evaluate:
+            if b is S.Zero and e is S.NegativeInfinity:
+                return S.ComplexInfinity
             if e is S.ComplexInfinity:
                 return S.NaN
             if e is S.Zero:
```

### Reconstructed oracle sites

- `site-0001`  sympy/core/power.py:291-296
  ```
     288:                 useinstead="Expr args",
     289:                 issue=19445,
     290:                 deprecated_since_version="1.7"
>>   291:             ).warn()
>>   292: 
>>   293:         if evaluate:
>>   294:             if e is S.ComplexInfinity:
>>   295:                 return S.NaN
>>   296:             if e is S.Zero:
     297:                 return S.One
     298:             elif e is S.One:
     299:                 return b
  ```

## pytest-dev__pytest-6116  (pytest-dev/pytest)

### Issue (problem_statement)

pytest --collect-only needs a one char shortcut command
I find myself needing to run `--collect-only` very often and that cli argument is a very long to type one. 

I do think that it would be great to allocate a character for it, not sure which one yet. Please use up/down thumbs to vote if you would find it useful or not and eventually proposing which char should be used. 

Clearly this is a change very easy to implement but first I want to see if others would find it useful or not.
pytest --collect-only needs a one char shortcut command
I find myself needing to run `--collect-only` very often and that cli argument is a very long to type one. 

I do think that it would be great to allocate a character for it, not sure which one yet. Please use up/down thumbs to vote if you would find it useful or not and eventually proposing which char should be used. 

Clearly this is a change very easy to implement but first I want to see if others would find it useful or not.

### Fix patch

```diff
diff --git a/src/_pytest/main.py b/src/_pytest/main.py
--- a/src/_pytest/main.py
+++ b/src/_pytest/main.py
@@ -109,6 +109,7 @@ def pytest_addoption(parser):
     group.addoption(
         "--collectonly",
         "--collect-only",
+        "--co",
         action="store_true",
         help="only collect tests, don't execute them.",
     ),
```

### Reconstructed oracle sites

- `site-0001`  src/_pytest/main.py:109-114
  ```
     106:     )
     107: 
     108:     group = parser.getgroup("collect", "collection")
>>   109:     group.addoption(
>>   110:         "--collectonly",
>>   111:         "--collect-only",
>>   112:         action="store_true",
>>   113:         help="only collect tests, don't execute them.",
>>   114:     ),
     115:     group.addoption(
     116:         "--pyargs",
     117:         action="store_true",
  ```

## scikit-learn__scikit-learn-10508  (scikit-learn/scikit-learn)

### Issue (problem_statement)

LabelEncoder transform fails for empty lists (for certain inputs)
Python 3.6.3, scikit_learn 0.19.1

Depending on which datatypes were used to fit the LabelEncoder, transforming empty lists works or not. Expected behavior would be that empty arrays are returned in both cases.

```python
>>> from sklearn.preprocessing import LabelEncoder
>>> le = LabelEncoder()
>>> le.fit([1,2])
LabelEncoder()
>>> le.transform([])
array([], dtype=int64)
>>> le.fit(["a","b"])
LabelEncoder()
>>> le.transform([])
Traceback (most recent call last):
  File "[...]\Python36\lib\site-packages\numpy\core\fromnumeric.py", line 57, in _wrapfunc
    return getattr(obj, method)(*args, **kwds)
TypeError: Cannot cast array data from dtype('float64') to dtype('<U32') according to the rule 'safe'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "[...]\Python36\lib\site-packages\sklearn\preprocessing\label.py", line 134, in transform
    return np.searchsorted(self.classes_, y)
  File "[...]\Python36\lib\site-packages\numpy\core\fromnumeric.py", line 1075, in searchsorted
    return _wrapfunc(a, 'searchsorted', v, side=side, sorter=sorter)
  File "[...]\Python36\lib\site-packages\numpy\core\fromnumeric.py", line 67, in _wrapfunc
    return _wrapit(obj, method, *args, **kwds)
  File "[...]\Python36\lib\site-packages\numpy\core\fromnumeric.py", line 47, in _wrapit
    result = getattr(asarray(obj), method)(*args, **kwds)
TypeError: Cannot cast array data from dtype('float64') to dtype('<U32') according to the rule 'safe'
```

### Fix patch

```diff
diff --git a/sklearn/preprocessing/label.py b/sklearn/preprocessing/label.py
--- a/sklearn/preprocessing/label.py
+++ b/sklearn/preprocessing/label.py
@@ -126,6 +126,9 @@ def transform(self, y):
         """
         check_is_fitted(self, 'classes_')
         y = column_or_1d(y, warn=True)
+        # transform of empty array is empty array
+        if _num_samples(y) == 0:
+            return np.array([])
 
         classes = np.unique(y)
         if len(np.intersect1d(classes, self.classes_)) < len(classes):
@@ -147,6 +150,10 @@ def inverse_transform(self, y):
         y : numpy array of shape [n_samples]
         """
         check_is_fitted(self, 'classes_')
+        y = column_or_1d(y, warn=True)
+        # inverse transform of empty array is empty array
+        if _num_samples(y) == 0:
+            return np.array([])
 
         diff = np.setdiff1d(y, np.arange(len(self.classes_)))
         if len(diff):
```

### Reconstructed oracle sites

- `site-0001`  sklearn/preprocessing/label.py:126-131
  ```
     123:         Returns
     124:         -------
     125:         y : array-like of shape [n_samples]
>>   126:         """
>>   127:         check_is_fitted(self, 'classes_')
>>   128:         y = column_or_1d(y, warn=True)
>>   129: 
>>   130:         classes = np.unique(y)
>>   131:         if len(np.intersect1d(classes, self.classes_)) < len(classes):
     132:             diff = np.setdiff1d(classes, self.classes_)
     133:             raise ValueError(
     134:                     "y contains previously unseen labels: %s" % str(diff))
  ```
- `site-0002`  sklearn/preprocessing/label.py:147-152
  ```
     144: 
     145:         Returns
     146:         -------
>>   147:         y : numpy array of shape [n_samples]
>>   148:         """
>>   149:         check_is_fitted(self, 'classes_')
>>   150: 
>>   151:         diff = np.setdiff1d(y, np.arange(len(self.classes_)))
>>   152:         if len(diff):
     153:             raise ValueError(
     154:                     "y contains previously unseen labels: %s" % str(diff))
     155:         y = np.asarray(y)
  ```

## matplotlib__matplotlib-23476  (matplotlib/matplotlib)

### Issue (problem_statement)

[Bug]: DPI of a figure is doubled after unpickling on M1 Mac
### Bug summary

When a figure is unpickled, it's dpi is doubled. This behaviour happens every time and if done in a loop it can cause an `OverflowError`.

### Code for reproduction

```python
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pickle
import platform

print(matplotlib.get_backend())
print('Matplotlib ver:', matplotlib.__version__)
print('Platform:', platform.platform())
print('System:', platform.system())
print('Release:', platform.release())
print('Python ver:', platform.python_version())


def dump_load_get_dpi(fig):
    with open('sinus.pickle','wb') as file:
        pickle.dump(fig, file)

    with open('sinus.pickle', 'rb') as blob:
        fig2 = pickle.load(blob)
    return fig2, fig2.dpi


def run():
    fig = plt.figure()
    x = np.linspace(0,2*np.pi)
    y = np.sin(x)

    for i in range(32):
        print(f'{i}: {fig.dpi}')
        fig, dpi = dump_load_get_dpi(fig)


if __name__ == '__main__':
    run()
```


### Actual outcome

```
MacOSX
Matplotlib ver: 3.5.2
Platform: macOS-12.4-arm64-arm-64bit
System: Darwin
Release: 21.5.0
Python ver: 3.9.12
0: 200.0
1: 400.0
2: 800.0
3: 1600.0
4: 3200.0
5: 6400.0
6: 12800.0
7: 25600.0
8: 51200.0
9: 102400.0
10: 204800.0
11: 409600.0
12: 819200.0
13: 1638400.0
14: 3276800.0
15: 6553600.0
16: 13107200.0
17: 26214400.0
18: 52428800.0
19: 104857600.0
20: 209715200.0
21: 419430400.0
Traceback (most recent call last):
  File "/Users/wsykala/projects/matplotlib/example.py", line 34, in <module>
    run()
  File "/Users/wsykala/projects/matplotlib/example.py", line 30, in run
    fig, dpi = dump_load_get_dpi(fig)
  File "/Users/wsykala/projects/matplotlib/example.py", line 20, in dump_load_get_dpi
    fig2 = pickle.load(blob)
  File "/Users/wsykala/miniconda3/envs/playground/lib/python3.9/site-packages/matplotlib/figure.py", line 2911, in __
[... truncated ...]

### Fix patch

```diff
diff --git a/lib/matplotlib/figure.py b/lib/matplotlib/figure.py
--- a/lib/matplotlib/figure.py
+++ b/lib/matplotlib/figure.py
@@ -3023,6 +3023,9 @@ def __getstate__(self):
         # Set cached renderer to None -- it can't be pickled.
         state["_cachedRenderer"] = None
 
+        # discard any changes to the dpi due to pixel ratio changes
+        state["_dpi"] = state.get('_original_dpi', state['_dpi'])
+
         # add version information to the state
         state['__mpl_version__'] = mpl.__version__
```

### Reconstructed oracle sites

- `site-0001`  lib/matplotlib/figure.py:3023-3028
  ```
    3020:         # re-attached to another.
    3021:         state.pop("canvas")
    3022: 
>>  3023:         # Set cached renderer to None -- it can't be pickled.
>>  3024:         state["_cachedRenderer"] = None
>>  3025: 
>>  3026:         # add version information to the state
>>  3027:         state['__mpl_version__'] = mpl.__version__
>>  3028: 
    3029:         # check whether the figure manager (if any) is registered with pyplot
    3030:         from matplotlib import _pylab_helpers
    3031:         if self.canvas.manager in _pylab_helpers.Gcf.figs.values():
  ```
