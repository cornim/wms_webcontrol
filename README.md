#Warema WMS Webcontrol Controller

This library can connect to a Warema WMS WebControl web server to send control commands.

Currently only vertical blinds are supported. Feel free to extend support to other devices.

Usage:

```python
from warema_wms import Shade

shades = Shade.get_all_shades()
shades[0].set_shade_position(25) #0=open; 100=closed
shades[1].get_shade_state(True) #Force update and get shade state
```

in case your WebControl server is not under `http://webcontrol.local` you'll 
have to create and pass your own WmsController.

```python
from warema_wms import WmsController, Shade

shades = Shade.get_all_shades(WmsController('http://server_addr'))
```

### Changes to version 0.2.0
- Made update procedure more resilient
- Introduced parameters to set number of retries and time between commands
- Set default time between commands to 0.1s
- Set default number of retries to 3

### Changes to version 0.1.4
- Removed bug on system were 'http://webcontrol.local' does not resolve

### Changes to version 0.1.2
- Reduced wait time between sending http commands to wms webcontrol webserver to 0.5 seconds

### Changes to version 0.1.1
- Changed package structure
- Improved documentation

### Changes to version 0.1.0
- Improved protocol
- Fixed bug where moving state was always true.