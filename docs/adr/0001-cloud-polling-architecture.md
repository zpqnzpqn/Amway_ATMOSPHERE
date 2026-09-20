# Cloud Polling over MQTT Long-Lived Push

For the initial integration architecture, we chose scheduled REST API polling (`cloud_polling`) via Home Assistant's `DataUpdateCoordinator` rather than a persistent AWS IoT MQTT WebSocket connection (`cloud_push`). Air purifier status metrics (filter life, PM2.5) change slowly, and REST polling eliminates complex WebSocket reconnection handling, AWS token expiry during standby, and connection drops on Home Assistant host restarts. Immediate state refresh is triggered upon user command dispatch.
