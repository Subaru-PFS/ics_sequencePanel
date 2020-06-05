import re

import pandas as pd
from pfs.utils.opdb import opDB


def visitsFromSet(visit_set_id):
    return opDB.fetchall(f'select pfs_visit_id from visit_set where visit_set_id={visit_set_id}')


def spsExposure(visits):
    columns = ['visit', 'exptype', 'specNum', 'arm', 'camId']
    dfs = [pd.DataFrame([], columns=columns)]
    for visit, in visits:
        try:
            exposures = opDB.fetchall(
                f'select sps_exposure.pfs_visit_id,exp_type,sps_module_id,arm,sps_exposure.sps_camera_id from sps_exposure inner join sps_visit on sps_exposure.pfs_visit_id=sps_visit.pfs_visit_id inner join sps_camera on sps_exposure.sps_camera_id = sps_camera.sps_camera_id where sps_exposure.pfs_visit_id={visit}')
            dfs.append(pd.DataFrame(exposures, columns=columns))

        except ValueError:
            pass

    return pd.concat(dfs, ignore_index=True)


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
