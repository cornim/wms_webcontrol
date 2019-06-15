#Warema WMS Webcontrol Controller

This library can connect to a Warema WMS WebControl web server to send control commands.

Currently only vertical blinds are supported. Feel free to extend support to other devices.

Usage:

```python
from wms_controller import Shade

shades = Shade.get_all_shades()
shades[0].set_shade_position(25) #0=open; 100=closed
shades[1].get_shade_state(True) #Force update and get shade state
```

in case your WebControl server is not under `http://webcontrol.local` you'll 
have to create and pass your own WmsController.

```python
from wms_controller import WmsController, Shade

shades = Shade.get_all_shades(WmsController(<http_addrs of your WebControl server>))
```

### Changes to version 0.1.0
- Improved protocol
- Fixed bug where moving state was always true.