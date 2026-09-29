ValueError: too many values to unpack (expected 2)

2026-09-29 18:26:33.339 Please replace `use_container_width` with `width`.


`use_container_width` will be removed after 2025-12-31.


For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'` or specify an integer width.

2026-09-29 18:26:44.613 Please replace `use_container_width` with `width`.


`use_container_width` will be removed after 2025-12-31.


For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'` or specify an integer width.

2026-09-29 18:26:56.211 Please replace `use_container_width` with `width`.


`use_container_width` will be removed after 2025-12-31.


For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'` or specify an integer width.

2026-09-29 18:26:57.707 Uncaught app execution

Traceback (most recent call last):

  File "/home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptrunner/exec_code.py", line 136, in exec_func_with_error_handling

    result = func()

             ^^^^^^

  File "/home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 909, in code_to_exec

    exec(code, module.__dict__)  # noqa: S102

    ^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/mount/src/tmr-colombia/app.py", line 127, in <module>

    ini, fin = rango_seleccionado

    ^^^^^^^^

ValueError: too many values to unpack (expected 2)
