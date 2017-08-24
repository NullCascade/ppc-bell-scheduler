# Pi Bell Scheduler
A bell scheduling program for the Raspberry Pi. This was written for an inexpensive replacement for a school's expensive bell system. The program maintains a school schedule in a json file, and will emit programmable patterns to a pin based on the defined schedule.

## Requirements
This module uses the [schedule module by Daniel Bader](https://pypi.python.org/pypi/schedule). Install it using `pip`:
```bash
pip install schedule
```

This was designed for the [pins on a Raspberry Pi 3b](http://pi4j.com/pins/model-3b-rev1.html). The pin definitions are board-based, not GPIO-based, and can be changed by modifying the following line:
```python
bellPins = [7, 11, 13]
```

## Usage
The program requires elevated privilages. The program takes a single parameter, which is the path to the configuration json file. Example usage:
```bash
cd ppc-bell-scheduler
sudo python bells.py bells.json
```

To ensure the script runs by default when the Pi starts, [add it to your rc.local file](https://www.raspberrypi.org/documentation/linux/usage/rc-local.md).
```bash
sudo python /home/pi/ppc-bell-scheduler/bells.py /home/pi/ppc-bell-scheduler/bells.json &
```

## Configuration
All configuration is done via a json file. The most bare-bones configuration to ring a bell at noon every Wednesday, plus on August 24th (which is a Thursday), looks like this:
```json
{
	"calendar": {
		"default": {
			"Wednesday": "noon_schedule"
		},
        "2017-08-24": "one_second_bell"
	},
	"schedules": {
		"noon_schedule": {
			"12:00": "one_sec_bell"
		}
	},
	"patterns": {
		"one_sec_bell": {
			"rings": 1,
			"duration": 1,
			"spacing": 0
		}
	}
}
```

A full example production schedule is shown in `bells.json`.

### Patterns
Patterns allow you to define when pins are activated. The program supports only basic patterns: you can define how many pin activations there will be with `rings`, how long the pins will be activated for with `duration`, and how long there will be between activations with `spacing`.

### Schedules
Schedules allow you to specify different types of days for the system to run on. In a school environment, you might have normal days, half-days, and a finals schedule.

Each schedule is a list of times, and the corresponding pattern to play at that time.

**Note: Leading zeroes are required in the schedule.**

### Calendar
This section has two parts. The first, the `default` table, has dates in a human-readable format: `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, and `Sunday`. If a day name is provided, with a schedule, it will use that schedule by default unless a different one is provided.

Additionally, specific dates can be provided in the `"YYYY-MM-DD"` format. Leading zeroes are required (example: `"2017-09-20"`). Dates provided here will overwrite the default schedule.

## Support
This program is provided as-is with no liability or support under the MIT license. If you encounter an issue, [submit a bug report](https://github.com/NullCascade/ppc-bell-scheduler/issues/new).

## License
This code is provided under the MIT license. See license.txt for details.
