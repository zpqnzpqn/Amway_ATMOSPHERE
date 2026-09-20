# HomeKit Air Purifier and Sensor Entity Mapping

To enable native Apple HomeKit control via Home Assistant's HomeKit Bridge without custom Homebridge plugins, the `amway_atmosphere` integration will adhere strictly to Home Assistant's standard `fan` and `sensor` platform specifications. 

The purifier entity will expose `FanEntityFeature.SET_SPEED` mapped linearly to percentages (Sky: 20% steps for 5 speeds; Mini: 33% steps for 3 speeds) and `FanEntityFeature.PRESET_MODE` for Auto, Night, and Turbo. Air quality `display.dust` (1–5) will be mapped directly to HomeKit's native 5-tier `AirQuality` characteristic, while individual filter percentages will be exposed as separate numeric sensors with the HEPA filter designated as the primary `FilterLifeLevel` for the main HomeKit Air Purifier accessory.
