from sqlalchemy import and_  # , or_

from .. import db, sql


class Article10(object):
    def get_environment_data(self, muids):
        mc = sql.MSFD10Target
        descr_nr = self.descriptor[1:]
        count, res = db.get_all_records(
            mc,
            and_(
                mc.Topic == 'EnvironmentalTarget',
                mc.ReportingFeature.like('%{}%'.format(descr_nr)),
                mc.MarineUnitID.in_(muids)
            )
        )

        if res:
            return res[0]
