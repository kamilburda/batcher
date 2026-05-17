"""Custom attributes for GEGL operations (layer effects) installed in GIMP."""

GEGL_OPERATIONS_AND_CUSTOM_ATTRIBUTES = {
  'gegl:add': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:alien-map': {
    'cpn-1-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'cpn-2-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'cpn-3-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'cpn-1-phaseshift': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'cpn-2-phaseshift': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'cpn-3-phaseshift': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:alpha-clip': {
    'low-limit': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'high-limit': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:apply-lens': {
    'refraction-index': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 10.0,
        'gamma': 3.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:bayer-matrix': {
    'subdivisions': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 15,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'x-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'amplitude': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'offset': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'exponent': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -512,
        'soft_maximum': 512,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'y-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -512,
        'soft_maximum': 512,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:bevel': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 8.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'elevation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 2.0
      }
    },
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 80,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'azimuth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 2.0
      }
    }
  },
  'gegl:bilateral-filter': {
    'blur-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'edge-preservation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:bloom': {
    'threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'softness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 2.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'strength': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:border-align': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'horizontal-margin': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'vertical-margin': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:box-blur': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:brightness-contrast': {
    'contrast': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'brightness': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:bump-map': {
    'azimuth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'elevation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.5,
        'soft_maximum': 90.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 65,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'offset-x': {
      'gui_type_kwargs': {
        'soft_minimum': -1000,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'offset-y': {
      'gui_type_kwargs': {
        'soft_minimum': -1000,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'waterlevel': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'ambient': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:c2g': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'samples': {
      'gui_type_kwargs': {
        'soft_minimum': 3,
        'soft_maximum': 17,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 30,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:cartoon': {
    'mask-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 50.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'pct-black': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:cell-noise': {
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'shape': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rank': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 3,
        'step_increment': 1,
        'page_increment': 2
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:channel-mixer': {
    'rr-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rg-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rb-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'gr-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'gg-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'gb-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'br-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'bg-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'bb-gain': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:checkerboard': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'x-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -128,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -128,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:color-assimilation-grid': {
    'grid-size': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 40.0,
        'gamma': 3.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'line-thickness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:color-exchange': {
    'red-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'green-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'blue-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:color-rotate': {
    'src-from': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'src-to': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'dest-from': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'dest-to': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'hue': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:color-temperature': {
    'original-temperature': {
      'gui_type_kwargs': {
        'soft_minimum': 1000.0,
        'soft_maximum': 12000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'intended-temperature': {
      'gui_type_kwargs': {
        'soft_minimum': 1000.0,
        'soft_maximum': 12000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:color-to-alpha': {
    'transparency-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'opacity-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:color-warp': {
    'weight-0': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-1': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-2': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-3': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-4': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-5': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-6': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight-7': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 220.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'weight': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'amount': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:contrast-curve': {
    'sampling-points': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 65536,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:convolution-matrix': {
    'a1': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'a2': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'a3': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'a4': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'a5': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'b1': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'b2': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'b3': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'b4': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'b5': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'c1': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'c2': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'c3': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'c4': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'c5': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'd1': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'd2': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'd3': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'd4': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'd5': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'e1': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'e2': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'e3': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'e4': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'e5': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'divisor': {
      'gui_type_kwargs': {
        'soft_minimum': -1000.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'offset': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:crop': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1024.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1024.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1024.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1024.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    }
  },
  'gegl:cubism': {
    'tile-size': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 256.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'tile-saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:deinterlace': {
    'size': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:denoise-dct': {
    'sigma': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:difference-of-gaussians': {
    'radius1': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'radius2': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:diffraction-patterns': {
    'red-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'green-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'blue-frequency': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'red-contours': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'green-contours': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'blue-contours': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'red-sedges': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'green-sedges': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'blue-sedges': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'brightness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'scattering': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'polarization': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:displace': {
    'amount-x': {
      'gui_type_kwargs': {
        'soft_minimum': -500.0,
        'soft_maximum': 500.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'amount-y': {
      'gui_type_kwargs': {
        'soft_minimum': -500.0,
        'soft_maximum': 500.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'center-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'center-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:distance-transform': {
    'threshold-lo': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'threshold-hi': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'averaging': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:dither': {
    'red-levels': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 65536,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'green-levels': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 65536,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'blue-levels': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 65536,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'alpha-levels': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 65536,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:divide': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:domain-transform': {
    'n-iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 5,
        'step_increment': 1,
        'page_increment': 2
      }
    },
    'spatial-factor': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'edge-preservation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:dropshadow': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -40.0,
        'soft_maximum': 40.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -40.0,
        'soft_maximum': 40.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 300.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 2.0
      }
    },
    'grow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': -50.0,
        'soft_maximum': 50.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 0.0
      }
    },
    'opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:edge-neon': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 50.0,
        'gamma': 2.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'amount': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 3.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:edge': {
    'amount': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:emboss': {
    'azimuth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'elevation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:engrave': {
    'row-height': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:exp-combine': {
    'steps': {
      'gui_type_kwargs': {
        'soft_minimum': 8,
        'soft_maximum': 32,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'sigma': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 32.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:exposure': {
    'black-level': {
      'gui_type_kwargs': {
        'soft_minimum': -0.1,
        'soft_maximum': 0.1,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'exposure': {
      'gui_type_kwargs': {
        'soft_minimum': -10.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:fattal02': {
    'alpha': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'beta': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'noise': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:fill-path': {
    'opacity': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:focus-blur': {
    'blur-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 2.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlight-factor': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'highlight-threshold-low': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'highlight-threshold-high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 5.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'focus': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'midpoint': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'aspect-ratio': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rotation': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:fractal-explorer': {
    'iter': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'zoom': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10000.0,
        'gamma': 1.5,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'shiftx': {
      'gui_type_kwargs': {
        'soft_minimum': -1000.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'shifty': {
      'gui_type_kwargs': {
        'soft_minimum': -1000.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'cx': {
      'gui_type_kwargs': {
        'soft_minimum': -2.5,
        'soft_maximum': 2.5,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'cy': {
      'gui_type_kwargs': {
        'soft_minimum': -2.5,
        'soft_maximum': 2.5,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'redstretch': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'greenstretch': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'bluestretch': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'ncolors': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 8192,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:fractal-trace': {
    'X1': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'X2': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'Y1': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'Y2': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'JX': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'JY': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'bailout': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:gamma': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:gaussian-blur-selective': {
    'blur-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'max-delta': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:gaussian-blur': {
    'std-dev-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.24,
        'soft_maximum': 100.0,
        'gamma': 3.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'std-dev-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.24,
        'soft_maximum': 100.0,
        'gamma': 3.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:gblur-1d': {
    'std-dev': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 3.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:gif-load': {
    'frame': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'frames': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'frame-delay': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:grid': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'x-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -64,
        'soft_maximum': 64,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -64,
        'soft_maximum': 64,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'line-width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'line-height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:high-pass': {
    'std-dev': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'contrast': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 5.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:hue-chroma': {
    'hue': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'chroma': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'lightness': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:illusion': {
    'division': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 64,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:image-compare': {
    'wrong-pixels': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'max-diff': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'avg-diff-wrong': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'avg-diff-total': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:inner-glow': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -30.0,
        'soft_maximum': 30.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 2.0,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -30.0,
        'soft_maximum': 30.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 2.0,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 30.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 3.0
      }
    },
    'grow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 30.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 0.0
      }
    },
    'opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'cover': {
      'gui_type_kwargs': {
        'soft_minimum': 50.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:jpg-save': {
    'quality': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'smoothing': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:json:dropshadow2': {
    'x': {
      'gui_type_kwargs': {}
    },
    'y': {
      'gui_type_kwargs': {}
    },
    'radius': {
      'gui_type_kwargs': {}
    },
    'opacity': {
      'gui_type_kwargs': {}
    }
  },
  'gegl:json:grey2': {
    'height': {
      'gui_type_kwargs': {}
    },
    'width': {
      'gui_type_kwargs': {}
    }
  },
  'gegl:layer': {
    'opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'scale': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:lens-blur': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 2.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlight-factor': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'highlight-threshold-low': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'highlight-threshold-high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:lens-distortion': {
    'main': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'edge': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'zoom': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'x-shift': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'y-shift': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'brighten': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:lens-flare': {
    'pos-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'pos-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:levels': {
    'in-low': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'in-high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'out-low': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'out-high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:linear-gradient': {
    'start-x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'start-y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'end-x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'end-y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:linear-sinusoid': {
    'x-period': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 256.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'y-period': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 256.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'x-amplitude': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y-amplitude': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x-phase': {
      'gui_type_kwargs': {
        'soft_minimum': -512.0,
        'soft_maximum': 512.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'y-phase': {
      'gui_type_kwargs': {
        'soft_minimum': -512.0,
        'soft_maximum': 512.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'offset': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'exponent': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -512.0,
        'soft_maximum': 512.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'y-offset': {
      'gui_type_kwargs': {
        'soft_minimum': -512.0,
        'soft_maximum': 512.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'rotation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'supersampling': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 8,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:local-threshold': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 1.0
      }
    },
    'aa-factor': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'low': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:long-shadow': {
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'length': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'midpoint': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'midpoint-rel': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:mantiuk06': {
    'contrast': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'detail': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 99.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:map-relative': {
    'scaling': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 5000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    }
  },
  'gegl:matting-global': {
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 200,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:maze': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:mblur': {
    'dampness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:mean-curvature-blur': {
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 60,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:median-blur': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'percentile': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'alpha-percentile': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:mirrors': {
    'm-angle': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'r-angle': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'n-segs': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 24,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'c-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'c-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'o-x': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'o-y': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'trim-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 0.5,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'trim-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 0.5,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'input-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'output-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:mix': {
    'ratio': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:mono-mixer': {
    'red': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'green': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'blue': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:mosaic': {
    'tile-size': {
      'gui_type_kwargs': {
        'soft_minimum': 5.0,
        'soft_maximum': 400.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'tile-height': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'tile-neatness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'color-variation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'tile-spacing': {
      'gui_type_kwargs': {
        'soft_minimum': 0.5,
        'soft_maximum': 30.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'light-dir': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:motion-blur-circular': {
    'center-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'center-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:motion-blur-linear': {
    'length': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 300.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:motion-blur-zoom': {
    'center-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'center-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'factor': {
      'gui_type_kwargs': {
        'soft_minimum': -0.5,
        'soft_maximum': 1.0,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:multiply': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:negative-darkroom': {
    'exposure': {
      'gui_type_kwargs': {
        'soft_minimum': -15.0,
        'soft_maximum': 5.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'expC': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'expM': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'expY': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'add-fog': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'boost-c': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 4.0,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'boost': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 4.0,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'boost-y': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 4.0,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'contrast-r': {
      'gui_type_kwargs': {
        'soft_minimum': 0.75,
        'soft_maximum': 1.5,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'contrast': {
      'gui_type_kwargs': {
        'soft_minimum': 0.75,
        'soft_maximum': 1.5,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'contrast-b': {
      'gui_type_kwargs': {
        'soft_minimum': 0.75,
        'soft_maximum': 1.5,
        'gamma': 2.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'dodge': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'flashC': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'flashM': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'flashY': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'illumX': {
      'gui_type_kwargs': {
        'soft_minimum': 0.7,
        'soft_maximum': 1.3,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'illumZ': {
      'gui_type_kwargs': {
        'soft_minimum': 0.7,
        'soft_maximum': 1.3,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:newsprint': {
    'period2': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle2': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'period3': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle3': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'period4': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle4': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'period': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'black-pullout': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'aa-samples': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 128,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'turbulence': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'blocksize': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 64.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angleboost': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 4.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:noise-cie-lch': {
    'holdness': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 8,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'lightness-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'chroma-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'hue-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:noise-hsv': {
    'holdness': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 8,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'hue-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'saturation-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'value-distance': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:noise-hurl': {
    'pct-random': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'repeat': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:noise-pick': {
    'pct-random': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'repeat': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:noise-reduction': {
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 8,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:noise-rgb': {
    'red': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'green': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'blue': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'alpha': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:noise-slur': {
    'pct-random': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'repeat': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:noise-solid': {
    'x-size': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 16.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'y-size': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 16.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'detail': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 15,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:noise-spread': {
    'amount-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 512,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'amount-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 512,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:normal-map': {
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 255.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:npd': {
    'square-size': {
      'gui_type_kwargs': {
        'soft_minimum': 5,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'rigidity': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'mls-weights-alpha': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:oilify': {
    'mask-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 25,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'exponent': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'intensities': {
      'gui_type_kwargs': {
        'soft_minimum': 8,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:opacity': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:pack': {
    'gap': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'align': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:panorama-projection': {
    'pan': {
      'gui_type_kwargs': {
        'soft_minimum': -360.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'tilt': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'spin': {
      'gui_type_kwargs': {
        'soft_minimum': -360.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'zoom': {
      'gui_type_kwargs': {
        'soft_minimum': 0.01,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:path': {
    'stroke-width': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'stroke-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'stroke-hardness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'fill-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:pdf-load': {
    'page': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'pages': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'ppi': {
      'gui_type_kwargs': {
        'soft_minimum': 10.0,
        'soft_maximum': 2400.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    }
  },
  'gegl:perlin-noise': {
    'alpha': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 4.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'zoff': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 8.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'n': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:photocopy': {
    'mask-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 50.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'sharpness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'black': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'white': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:piecewise-blend': {
    'levels': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'gamma': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:pixelize': {
    'size-x': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 2048,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'size-y': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 2048,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'offset-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 2048,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'offset-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 2048,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'ratio-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'ratio-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:plasma': {
    'turbulence': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 7.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -4096,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -4096,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:png-save': {
    'compression': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 9,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'bitdepth': {
      'gui_type_kwargs': {
        'soft_minimum': 8,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:polar-coordinates': {
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'pole-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'pole-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:posterize': {
    'levels': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 64,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:ppm-save': {
    'bitdepth': {
      'gui_type_kwargs': {
        'soft_minimum': 8,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:radial-gradient': {
    'start-x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'start-y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'end-x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'end-y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:rectangle': {
    'x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:recursive-transform': {
    'first-iteration': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'fade-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:red-eye-removal': {
    'threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 0.8,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:reflect': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:reinhard05': {
    'brightness': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'chromatic': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'light': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:reset-origin': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    }
  },
  'gegl:rgb-clip': {
    'low-limit': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'high-limit': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:ripple': {
    'amplitude': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 2.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'period': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'phi': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'angle': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:rotate-on-center': {
    'near-z': {
      'gui_type_kwargs': {}
    },
    'degrees': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'origin-x': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'origin-y': {
      'gui_type_kwargs': {
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:rotate': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'degrees': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:saturation': {
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:scale-ratio': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:scale-size-keepaspect': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:scale-size': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -9000.0,
        'soft_maximum': 9000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    }
  },
  'gegl:seamless-clone-compose': {
    'max-refine-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'xoff': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'yoff': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:seamless-clone': {
    'max-refine-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'xoff': {
      'gui_type_kwargs': {
        'soft_minimum': -100000,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'yoff': {
      'gui_type_kwargs': {
        'soft_minimum': -100000,
        'soft_maximum': 100000,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:sepia': {
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:shadows-highlights-correction': {
    'shadows': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlights': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'whitepoint': {
      'gui_type_kwargs': {
        'soft_minimum': -10.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'compress': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'shadows-ccorrect': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlights-ccorrect': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:shadows-highlights': {
    'shadows': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlights': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'whitepoint': {
      'gui_type_kwargs': {
        'soft_minimum': -10.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'compress': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'shadows-ccorrect': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'highlights-ccorrect': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:shear': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -100.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:shift': {
    'shift': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 200,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:simplex-noise': {
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 20,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:sinus': {
    'x-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'y-scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'complexity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 15.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'blend-power': {
      'gui_type_kwargs': {
        'soft_minimum': -7.5,
        'soft_maximum': 7.5,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:slic': {
    'cluster-size': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 1024,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'compactness': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 40,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 15,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:snn-mean': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 40,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'pairs': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 2,
        'step_increment': 1,
        'page_increment': 2
      }
    }
  },
  'gegl:softglow': {
    'glow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 50.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'brightness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'sharpness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:spherize': {
    'angle-of-view': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'curvature': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'amount': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:spiral': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 400.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'base': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 20.0,
        'gamma': 2.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'balance': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rotation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 4096,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:stereographic-projection': {
    'pan': {
      'gui_type_kwargs': {
        'soft_minimum': -360.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'tilt': {
      'gui_type_kwargs': {
        'soft_minimum': -180.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'spin': {
      'gui_type_kwargs': {
        'soft_minimum': -360.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'zoom': {
      'gui_type_kwargs': {
        'soft_minimum': 0.01,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'height': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 10000,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:stress': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 2,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'samples': {
      'gui_type_kwargs': {
        'soft_minimum': 3,
        'soft_maximum': 17,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'iterations': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 30,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:styles': {
    'outline-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'outline-x': {
      'gui_type_kwargs': {
        'soft_minimum': -15.0,
        'soft_maximum': 15.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'outline-y': {
      'gui_type_kwargs': {
        'soft_minimum': -15.0,
        'soft_maximum': 15.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'outline-blur': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 3.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 3.0
      }
    },
    'outline': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 0.0
      }
    },
    'shadow-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'shadow-x': {
      'gui_type_kwargs': {
        'soft_minimum': -40.0,
        'soft_maximum': 40.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'shadow-y': {
      'gui_type_kwargs': {
        'soft_minimum': -40.0,
        'soft_maximum': 40.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 3.0
      }
    },
    'shadow-grow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 50.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 0.0
      }
    },
    'shadow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 110.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 2.0
      }
    },
    'bevel-depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'bevel-elevation': {
      'gui_type_kwargs': {
        'soft_minimum': 55.0,
        'soft_maximum': 125.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'bevel-azimuth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 2.0
      }
    },
    'bevel-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 8.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'bevel-outlow': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 0.2,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'bevel-outhigh': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 1.2,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'bevel-dark': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'ig-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 30.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 3.0
      }
    },
    'ig-grow-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 30.0,
        'gamma': 1.5,
        'step_increment': 1.0,
        'page_increment': 5.0,
        'digits': 0.0
      }
    },
    'ig-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'ig-treatment': {
      'gui_type_kwargs': {
        'soft_minimum': 50.0,
        'soft_maximum': 85.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'image-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'image-saturation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 3.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'image-lightness': {
      'gui_type_kwargs': {
        'soft_minimum': -20.0,
        'soft_maximum': 20.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'os-depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'os-elevation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 180.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    },
    'os-azimuth': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 2.0
      }
    },
    'os-radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 8.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'os-src-opacity': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'os-outlow': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 0.2,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'os-outhigh': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 1.2,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    },
    'os-dark': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 0.5,
        'digits': 3.0
      }
    }
  },
  'gegl:subtract': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:supernova': {
    'center-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'center-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 1000,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'spokes-count': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 1024,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'random-hue': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 360,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:svg-load': {
    'width': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'height': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:text': {
    'size': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2048.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'wrap': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 1000000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'vertical-wrap': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 1000000,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'alignment': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 2,
        'step_increment': 1,
        'page_increment': 2
      }
    },
    'vertical-alignment': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 2,
        'step_increment': 1,
        'page_increment': 2
      }
    },
    'width': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'height': {
      'gui_type_kwargs': {
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:texturize-canvas': {
    'depth': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:threshold': {
    'value': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'high': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:tiff-load': {
    'directory': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 16,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:tiff-save': {
    'bitdepth': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 64,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'fp': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 1,
        'step_increment': 1,
        'page_increment': 2
      }
    }
  },
  'gegl:tile-glass': {
    'tile-width': {
      'gui_type_kwargs': {
        'soft_minimum': 5,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'tile-height': {
      'gui_type_kwargs': {
        'soft_minimum': 5,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:tile-paper': {
    'tile-width': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 1500,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'tile-height': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 1500,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'move-rate': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:tile': {
    'offset-x': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 1024,
        'step_increment': 1,
        'page_increment': 100
      }
    },
    'offset-y': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 1024,
        'step_increment': 1,
        'page_increment': 100
      }
    }
  },
  'gegl:transform': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    }
  },
  'gegl:translate': {
    'origin-x': {
      'gui_type_kwargs': {}
    },
    'origin-y': {
      'gui_type_kwargs': {}
    },
    'near-z': {
      'gui_type_kwargs': {}
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': -1000.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': -1000.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    }
  },
  'gegl:unsharp-mask': {
    'std-dev': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 40.0,
        'gamma': 3.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'scale': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 3.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:value-propagate': {
    'lower-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'upper-threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rate': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:variable-blur': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 2.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:vector-stroke': {
    'width': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 200.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'opacity': {
      'gui_type_kwargs': {
        'soft_minimum': -2.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:vignette': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 3.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'softness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'gamma': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'proportion': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'squeeze': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'rotation': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 360.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 2.0
      }
    }
  },
  'gegl:warp': {
    'strength': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    },
    'size': {
      'gui_type_kwargs': {
        'soft_minimum': 1.0,
        'soft_maximum': 10000.0,
        'gamma': 1.0,
        'step_increment': 0.1,
        'page_increment': 1.0,
        'digits': 1.0
      }
    },
    'hardness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'spacing': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 100.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:waterpixels': {
    'size': {
      'gui_type_kwargs': {
        'soft_minimum': 8,
        'soft_maximum': 256,
        'step_increment': 1,
        'page_increment': 10
      }
    },
    'smoothness': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 10.0,
        'gamma': 1.5,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    },
    'regularization': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    }
  },
  'gegl:watershed-transform': {
    'flag-component': {
      'gui_type_kwargs': {
        'soft_minimum': -1,
        'soft_maximum': 4,
        'step_increment': 1,
        'page_increment': 2
      }
    }
  },
  'gegl:wavelet-blur-1d': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 256.0,
        'gamma': 3.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:wavelet-blur': {
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 256.0,
        'gamma': 3.0,
        'step_increment': 1.0,
        'page_increment': 10.0,
        'digits': 2.0
      }
    }
  },
  'gegl:waves': {
    'x': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'y': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'amplitude': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'period': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 1000.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 100.0,
        'digits': 1.0
      }
    },
    'phi': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'aspect': {
      'gui_type_kwargs': {
        'soft_minimum': 0.1,
        'soft_maximum': 10.0,
        'gamma': 1.0,
        'step_increment': 0.01,
        'page_increment': 1.0,
        'digits': 3.0
      }
    }
  },
  'gegl:webp-save': {
    'quality': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  },
  'gegl:whirl-pinch': {
    'whirl': {
      'gui_type_kwargs': {
        'soft_minimum': -720.0,
        'soft_maximum': 720.0,
        'gamma': 1.0,
        'step_increment': 1.0,
        'page_increment': 15.0,
        'digits': 1.0
      }
    },
    'pinch': {
      'gui_type_kwargs': {
        'soft_minimum': -1.0,
        'soft_maximum': 1.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    },
    'radius': {
      'gui_type_kwargs': {
        'soft_minimum': 0.0,
        'soft_maximum': 2.0,
        'gamma': 1.0,
        'step_increment': 0.001,
        'page_increment': 0.1,
        'digits': 3.0
      }
    }
  },
  'gegl:wind': {
    'threshold': {
      'gui_type_kwargs': {
        'soft_minimum': 0,
        'soft_maximum': 50,
        'step_increment': 1,
        'page_increment': 5
      }
    },
    'strength': {
      'gui_type_kwargs': {
        'soft_minimum': 1,
        'soft_maximum': 100,
        'step_increment': 1,
        'page_increment': 10
      }
    }
  }
}
