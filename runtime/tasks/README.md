# runtime/tasks/

Layer D task-local memory store.

Task contexts under `active/` are scoped to one active task, workspace, or run.
They are not durable user memory, runtime memory, or canonical knowledge unless
explicitly promoted through a governed pass.

Layout:

```text
runtime/tasks/
  _schema.json
  active/
  archive/
```

The current pass creates the substrate and inspector support. It does not yet
auto-create task contexts for every workflow.
