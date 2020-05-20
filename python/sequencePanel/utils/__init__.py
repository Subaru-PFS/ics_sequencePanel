import re

from pfs.utils.spectroIds import SpectroIds


def stripQuotes(txt):
    """ Strip quotes from string """
    return txt.replace('"', "'").strip()


def stripField(rawCmd, field):
    """ Strip given text field from rawCmd """
    if re.search(field, rawCmd) is None:
        return rawCmd
    idlm = re.search(field, rawCmd).span(0)[-1]
    sub = rawCmd[idlm:]
    sub = sub if sub.find(' ') == -1 else sub[:sub.find(' ')]
    pattern = f' {field}{sub[0]}(.*?){sub[0]}' if sub[0] in ['"', "'"] else f' {field}{sub}'
    m = re.search(pattern, rawCmd)
    return rawCmd.replace(m.group(), '').strip()


def camMask(mask):
    mask = int(mask, 0)
    allCams = [SpectroIds(f'{arm}{specNum}') for arm in SpectroIds.validArms for specNum in SpectroIds.validModules]

    cams = []
    for cam in allCams:
        bit = cam.camId - 1
        if bool((mask & 1 << bit) >> bit):
            cams.append(cam)

    return cams
