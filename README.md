# parasol
Parallel outdoor testing of solar modules.

`parasol` schedules periodic JV scans for multiple modules. Modules can be added and removed from the scheduler as necessary.

## Example code

```
import parasol

c = parasol.Controller(rootdir = "filepath_to_save_in")

c.load_module(
  id = 1, #relay index
  name = "Module1", #name of the sample for filenaming
  area = 10.2, #cell area, cm2
  interval = 15*60, #interval between scans, seconds
  vmin = -0.1, #scan range, volts
  vmax = 1.2,
  steps = 121,
  )
```

This will start recording JV scans on relay 1 every 15 minutes. 

We can then add another module at any time
```
c.load_module(
  id = 2, #relay index
  name = "Module2", #name of the sample for filenaming
  area = 10.2, #cell area, cm2
  interval = 15*60, #interval between scans, seconds
  vmin = -0.1, #scan range, volts
  vmax = 1.2,
  steps = 121,
  )
```

and remove modules by the relay index

```
c.unload_module(
  id = 1, #relay index
  )
```

