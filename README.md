collectd_nvidia_smi
===================

Python plugin for collectd that reads metrics from `nvidia-smi`.

## Alternative

`collectd` already has a gpu_nvidia plugin built-in written in C that queries NVIDIA devices using NVML. However, it pins down which metrics can be gathered, while `collectd_nvidia_smi` allows any metric to be queried from the `nvidia-smi` binary.

## Metrics

Some useful examples from `nvidia-smi --help-query-gpu`:

	"fan.speed"
	The fan speed value is the percent of maximum speed that the device's fan is currently intended to run at. It ranges from 0 to 100 %. Note: The reported speed is the intended fan speed. If the fan is physically blocked and unable to spin, this output will not match the actual fan speed. Many parts do not report fan speeds because they rely on cooling via fans in the surrounding enclosure.

	"memory.total"
	Total installed GPU memory.

	"memory.used"
	Total memory allocated by active contexts.

	"memory.free"
	Total free memory.

	"utilization.gpu"
	Percent of time over the past sample period during which one or more kernels was executing on the GPU.
	The sample period may be between 1 second and 1/6 second depending on the product.

	"utilization.memory"
	Percent of time over the past sample period during which global (device) memory was being read or written.
	The sample period may be between 1 second and 1/6 second depending on the product.

	"temperature.gpu"
	 Core GPU temperature. in degrees C.

	"temperature.memory"
	 HBM memory temperature. in degrees C.

	"power.draw"
	The last measured power draw for the entire board, in watts. Only available if power management is supported. This reading is accurate to within +/- 5 watts.

	"power.limit"
	The software power limit in watts. Set by software like nvidia-smi. On Kepler devices Power Limit can be adjusted using [-pl | --power-limit=] switches.

	"clocks.current.graphics" or "clocks.gr"
	Current frequency of graphics (shader) clock.

	"clocks.current.sm" or "clocks.sm"
	Current frequency of SM (Streaming Multiprocessor) clock.

	"clocks.current.memory" or "clocks.mem"
	Current frequency of memory clock.

	"clocks.current.video" or "clocks.video"
	Current frequency of video encoder/decoder clock.

	"clocks.max.graphics" or "clocks.max.gr"
	Maximum frequency of graphics (shader) clock.

	"clocks.max.sm" or "clocks.max.sm"
	Maximum frequency of SM (Streaming Multiprocessor) clock.

	"clocks.max.memory" or "clocks.max.mem"
	Maximum frequency of memory clock.

## Example

Here is an example on how to configure the plugin. Put the on `collectd.conf`:

```
[...]
LoadPlugin python
<Plugin python>
    ModulePath "/opt/collectd_plugins/python" # Where you put the python file
    Import "collectd_nvidia_smi"              # Python file name
    <Module collectd_nvidia_smi>
    	Bin "/usr/bin/nvidia-smi" # Optional
        QueryGPU "utilization.gpu"
        QueryGPU "utilization.memory"
    </Module>
</Plugin>
[...]
```

If you are running `collectd` as root or whatever other user, make sure you can run `nvidia-smi` with such user, or else it won't work. For example, it may be necessary to set LD_LIBRARY_PATH to find NVIDIA's libraries.

## TODO

 - Allow to select which ids to monitor.
 - Perhaps include an option to use `nvidia-smi -q -x` instead. Keeping in mind that the queries will be different (different names).

## LICENSE

MIT
