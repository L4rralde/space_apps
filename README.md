# Quijo-Team

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/L4rralde/space_apps/HEAD)

Main algorithm is defined in [class Predictor](https://github.com/L4rralde/space_apps/blob/3470bc01d3bb0343ff75cc123294fa93587a7ab4/model/codigo.py#L139)

It interfaces our apps and scripts via [Prediction](https://github.com/L4rralde/space_apps/blob/3470bc01d3bb0343ff75cc123294fa93587a7ab4/model/codigo.py#L109C7-L109C17) objects, which includes all the information used by all the pipe stages of our algorithm.

## Requirements:
- Unix-based environment
- python3 with pip3 up to date.


Before running any app/script, run the following script:

```sh
source scripts/set_space.sh
```

### Install

If your environment met the requirements:

```sh
git clone https://github.com/L4rralde/space_apps.git
cd space_apps
pip install -r requirements.txt
```

## Or try on Binder

Our project has been prepared to run on Binder. By opting this option, it is possible to launch it on a web browser with no need of any prior installation. [Go and try it yourself](https://mybinder.org/v2/gh/L4rralde/space_apps/HEAD).


### Contributors
- Alejandro Negrete
- Emmanuel Larralde
- Isaac Barrón
- Isaac Mauricio
- Miriam Calderón
- Ramsses De los Santos
