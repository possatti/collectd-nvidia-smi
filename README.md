nvsmi
=====

This is a python plugin for `collectd` which reads metrics from `nvidia-smi --query-gpu`.

**UPDATE: I am no longer interested in maintaining this repository, since I am now using Telegraf. You can still use this if you like it and if it works for you, but I recommend you take a look at the *Alternatives* section below.**

## Alternatives

`collectd` already has a `gpu_nvidia` plugin written in C that queries NVIDIA devices using NVML. However, it pins down which metrics can be collected, while my plugin allows any metric to be queried from the `nvidia-smi` binary. Also, the `gpu_nvidia` plugin doesn't seem to be bundled with `collectd` when installing it from `apt-get`.

Before developing this plugin, I also used [nvidia2graphite](https://github.com/stefan-k/nvidia2graphite) for some time, which can be used to collect and send GPU usage directly to Graphite.

And, my new favorite (the one I am currently using): Telegraf (instead of `collectd`) with its `nvidia_smi` plugin. It has been working pretty well for me.

## Installing and configuring

I'm not aware of any convention to where python plugins should be installed to. The good news is that you can actually install them wherever you want, as long as you configure `collectd` accordingly.

I suggest you copy the `nvsmi.py` script (this is the python plugin) to `/opt/collectd/python/nvsmi.py` (you'll probably have to create the directories). And then configure your `collectd.conf` like this:

```
[...]
LoadPlugin python
<Plugin python>
    ModulePath "/opt/collectd/python" # Where you put the python file.
    Import "nvsmi"                    # The name of the script.
    <Module nvsmi>
        ## (Optional) In case 'nvidia-smi' is not on your 'PATH'.
        #Bin "/usr/bin/nvidia-smi"

        ## (Optional) Set the read interval here. It defaults to the `Interval`
        ## of the python plugin.
        Interval 30

        ## You can have any number of queries per line.
        QueryGPU "temperature.gpu"
        QueryGPU "power.draw" "power.limit"
        QueryGPU "utilization.gpu" "utilization.memory"
        QueryGPU "memory.total" "memory.used" "memory.free"

        ## You can replace complicated names with simpler ones.
        #Replace "clocks_throttle_reasons" "ctr"

        ## You can replace dots and underlines from query names with whatever you want.
        #ReplaceDotWith "|"
        #ReplaceUnderlineWith "-"

        ## WARN: Replacements are applied on the same order you provide here in
        ##       the configuration.
    </Module>
</Plugin>
[...]
```

Make sure that, whatever user `collectd` is running on, it can read the `nvsmi.py` script, and that `nvidia-smi` works for that user. It may be necessary to set `LD_LIBRARY_PATH` properly, so that `nvidia-smi` can find NVIDIA's dynamic libraries, for example.

Also check if the queries you want to use have actually valid values for your GPUs, i.e., they are actual numbers or they have a converter for them. Read more on converters down bellow.

## Metrics

Some useful queries from `nvidia-smi --help-query-gpu`:

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

## Converters

Some values output by `nvidia-smi` need conversion to an integer or float value. For example, `pci.bus`, and many other queries, need to be converted from base 16 to base 10. `display_mode`, and many others, are either `Enabled` or `Disabled`, so they are converted to `1` or `0`, respectively. Other values seem impossible to convert, like `name`, `driver_version`, `pci.bus_id`, but I don't think there is anyone trying to watch these with `collectd`, so just be aware that they won't work.

There are also some other queries that my GPU does not support, so I could not prepare them adequately, because I didn't know what they looked like, and I was not in the mood for reading a bunch of docs for queries I'm not going to use. There is no restriction to which queries you can make though.

<!-- By default any value is considered a "gauge", except those that I know what they are. -->

## Future improvements

Here is a list of what I plan to do if I actually feel like doing it:

 - Allow to select which GPUs to monitor.
 - Allow different queries for each GPU. (I should pay attention to make a single `nvidia-smi` call.)
 - Perhaps include an option to use `nvidia-smi -q -x` instead. Keeping in mind that the queries will be different (different names).

## LICENSE

MIT
