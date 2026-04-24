# Adapters

UseCaseCore keeps integrations at the edge of the use-case model.

The initial scaffold includes protocols for:

- policy engines
- transition/state-machine libraries
- event buses
- job queues
- workflow engines

Adapters should translate a tool into UseCaseCore's execution vocabulary without
making use cases depend on framework-specific details.

For `v0.1.0`, adapter protocols stay intentionally small. A concrete adapter
should usually expose one operation, such as `allowed()`, `publish()`,
`enqueue()`, or `start()`, and let the use case keep ownership of business
ordering.
