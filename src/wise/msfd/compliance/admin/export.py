# pylint: skip-file
"""CSV export views for compliance assessments."""
from __future__ import absolute_import

import csv
import re
from io import BytesIO

import six

from wise.msfd.compliance.admin.admin import AdminScoring
from wise.msfd.compliance.assessment import (
    ARTICLE_WEIGHTS, CONCLUSION_COLOR_TABLE,
)
from wise.msfd.compliance.interfaces import INationalDescriptorAssessment
from plone.api.portal import get_tool
from wise.msfd.compliance.scoring import OverallScores


class ExportScores2024CSV(AdminScoring):
    """Export 2024 scores as CSV"""

    SCORE_COLORS = {
        0: '#eeeeee',
        1: '#00b400',
        2: '#96eb96',
        3: '#ff5a5a',
        4: '#ffcc99',
        5: '#ff9696',
        6: '#b8d1e0',
    }

    QUESTION_SCORE_COLORS = {
        '1': '#00b400',
        '0.75': '#96eb96',
        '0.5': '#ffcc99',
        '0.25': '#ff9696',
        '0': '#ff5a5a',
        '0.250': '#b8d1e0',
        '/': '#eeeeee',
    }

    CHANGE_COLORS = {
        -2: '#ff5a5a',
        -1: '#ff9696',
        0: '#ffcc99',  # eeeeee
        0.1: '#ffcc99',  # eeeeee
        1: '#d7ffd7',
        2: '#96eb96',
        3: '#00b400',
        4: '#00b400',
    }

    DESCRIPTOR_ORDER = ['D2', 'D5', 'D7', 'D8', 'D9', 'D10', 'D11',
                        'D1B', 'D1M', 'D1R', 'D1F', 'D1C',
                        'D3', 'D1P', 'D6', 'D4']

    def _get_question_score(self, data, article_title, question_id):
        """Extract score value for a specific question from assessment data"""
        key = '{}_{}_Score'.format(article_title, question_id)
        score_obj = data.get(key)
        if not score_obj or not score_obj.values:
            return 0
        v = score_obj.values[0]
        return score_obj.question.scores[v]

    def _get_question_score_color(self, data, article_title, question_id):
        """Get hex color for a specific question score"""
        score = self._get_question_score(data, article_title, question_id)
        if score == 0:
            return self.SCORE_COLORS[0]
        return self.QUESTION_SCORE_COLORS.get(str(score), '#eeeeee')

    def _get_phase_score(self, obj, article_title, phase):
        """Get phase score percentage using OverallScores"""
        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):
            return 0
        data = obj.saved_assessment_data.last()
        phase_scores = OverallScores(ARTICLE_WEIGHTS, article_title)
        phase_scores = self._setup_phase_overall_scores(
            phase_scores, data, article_title)
        return phase_scores.get_score_for_phase(phase)

    def _get_phase_score_color(self, obj, article_title, phase):
        """Get hex color for a phase score"""
        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):
            return self.SCORE_COLORS[0]
        data = obj.saved_assessment_data.last()
        phase_scores = OverallScores(ARTICLE_WEIGHTS, article_title)
        phase_scores = self._setup_phase_overall_scores(
            phase_scores, data, article_title)
        # use the color already computed by _setup_phase_overall_scores,
        # which distinguishes 'Not relevant' (max_score == 0 -> color 0)
        # from 'Not reported' (score 0 -> color 3); recomputing the range
        # index here collapses both cases to 'Not reported'
        color_index = getattr(phase_scores, phase)['color']
        return self.SCORE_COLORS.get(color_index, '#eeeeee')

    def _get_phase_range_index(self, obj, article_title, phase):
        """Get phase range index (0-4) using OverallScores"""
        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):
            return 0
        data = obj.saved_assessment_data.last()
        phase_scores = OverallScores(ARTICLE_WEIGHTS, article_title)
        phase_scores = self._setup_phase_overall_scores(
            phase_scores, data, article_title)
        return phase_scores.get_range_index_for_phase(phase)

    def _get_change_color(self, change_value):
        """Get hex color for a change value"""
        return self.CHANGE_COLORS.get(change_value, '#eeeeee')

    def __call__(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        rows = []
        seen = set()

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            if not INationalDescriptorAssessment.providedBy(obj):
                continue

            article_title = obj.title
            if article_title not in ('Art8-2024', 'Art9-2024', 'Art10-2024'):
                continue

            descriptor_folder = obj.aq_parent
            region_folder = descriptor_folder.aq_parent
            country_folder = region_folder.aq_parent

            key = (country_folder.id, region_folder.id, descriptor_folder.id)
            if key in seen:
                continue
            seen.add(key)

            art8_2024 = descriptor_folder.get('art8-2024')
            art9_2024 = descriptor_folder.get('art9-2024')
            art9 = descriptor_folder.get('art9')

            art9_comp_2024 = self._get_phase_range_index(
                art9_2024, 'Art9-2024', 'completeness')
            art9_adeq_2018 = self._get_phase_range_index(
                art9, 'Art9', 'adequacy')
            art9_adequacy_change = art9_comp_2024 - art9_adeq_2018
            if art9_adequacy_change == 0:
                art9_adequacy_change = 0.1
            art9_adequacy_change_color = self._get_change_color(
                art9_adequacy_change)

            art9_completeness_score = self._get_phase_score(
                art9_2024, 'Art9-2024', 'completeness')
            if art9_completeness_score == 0:
                art9_completeness_score = 2
            art9_completeness_score_color = self._get_phase_score_color(
                art9_2024, 'Art9-2024', 'completeness')

            art9_adequacy_score = self._get_phase_score(
                art9_2024, 'Art9-2024', 'adequacy')
            if art9_adequacy_score == 0:
                art9_adequacy_score = 2
            art9_adequacy_score_color = self._get_phase_score_color(
                art9_2024, 'Art9-2024', 'adequacy')

            art8_consistency = self._get_phase_score(
                art8_2024, 'Art8-2024', 'consistency')
            if art8_consistency == 0:
                art8_consistency = 2
            art8_consistency_color = self._get_phase_score_color(
                art8_2024, 'Art8-2024', 'consistency')

            art9_q4_score = 0
            art9_q6_score = 0
            art9_q4_color = self.SCORE_COLORS[0]
            art9_q6_color = self.SCORE_COLORS[0]
            if (art9_2024 and hasattr(art9_2024, 'saved_assessment_data')
                    and art9_2024.saved_assessment_data):
                data = art9_2024.saved_assessment_data.last()
                art9_q4_score = self._get_question_score(
                    data, 'Art9-2024', 'A09Q4')
                art9_q6_score = self._get_question_score(
                    data, 'Art9-2024', 'A09Q6')
                art9_q4_color = self._get_question_score_color(
                    data, 'Art9-2024', 'A09Q4')
                art9_q6_color = self._get_question_score_color(
                    data, 'Art9-2024', 'A09Q6')

            rows.append({
                'country_code': country_folder.id.upper(),
                'country_name': country_folder.title,
                'region_code': region_folder.id.upper(),
                'region_name': region_folder.title,
                'descriptor_code': self._map_descriptor_code(
                    descriptor_folder.id.upper()),
                'descriptor_name': descriptor_folder.title,
                'art9_adequacy_change': art9_adequacy_change,
                'art9_adequacy_change_color': art9_adequacy_change_color,
                'art9_completeness_score': art9_completeness_score,
                'art9_completeness_score_color': art9_completeness_score_color,
                'art9_adequacy_score': art9_adequacy_score,
                'art9_adequacy_score_color': art9_adequacy_score_color,
                'art8_consistency_score': art8_consistency,
                'art8_consistency_score_color': art8_consistency_color,
                'art9_q4_score': art9_q4_score,
                'art9_q4_score_color': art9_q4_color,
                'art9_q6_score': art9_q6_score,
                'art9_q6_score_color': art9_q6_color,
            })

        def _sort_key(row):
            try:
                desc_idx = self.DESCRIPTOR_ORDER.index(
                    row['descriptor_code'])
            except ValueError:
                desc_idx = 999
            return (row['country_code'], desc_idx)

        rows.sort(key=_sort_key)
        output = BytesIO()
        fieldnames = [
            'country_code', 'country_name', 'region_code', 'region_name',
            'descriptor_code', 'descriptor_name',
            'art9_adequacy_change', 'art9_adequacy_change_color',
            'art9_completeness_score', 'art9_completeness_score_color',
            'art9_adequacy_score', 'art9_adequacy_score_color',
            'art8_consistency_score', 'art8_consistency_score_color',
            'art9_q4_score', 'art9_q4_score_color',
            'art9_q6_score', 'art9_q6_score_color',
        ]

        if six.PY2:
            import cStringIO
            text_output = cStringIO.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue())
        else:
            import io
            text_output = io.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue().encode('utf-8'))

        output.seek(0)
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=scores_2024.csv'
        )
        return output.read()


class ExportArt9Q5Q6CSV(AdminScoring):
    """Export Art9-2024 Q4, Q5 and Q6 score counts by descriptor and region as CSV"""

    QUESTION_SCORE_COLORS = {
        '1': '#00b400',
        '0.75': '#96eb96',
        '0.5': '#ffcc99',
        '0.25': '#ff9696',
        '0': '#ff5a5a',
        '0.250': '#b8d1e0',
        '/': '#eeeeee',
    }

    ALL_SCORES = ['1', '0.5', '0.25', '0', '0.250', '/']

    SCORE_LABELS = {
        '1': 'Very good',
        '0.5': 'Moderate',
        '0.25': 'Poor',
        '0': 'Not reported',
        '0.250': 'Not clear',
        '/': 'Not relevant',
    }

    SCORE_ORDER = ['Very good', 'Moderate', 'Poor',
                   'Not reported', 'Not clear', 'Not relevant']

    DESCRIPTOR_ORDER = ['D2', 'D5', 'D7', 'D8', 'D9', 'D10', 'D11',
                        'D1B', 'D1M', 'D1R', 'D1F', 'D1C',
                        'D3', 'D1P', 'D6', 'D4']

    def __call__(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        seen = set()
        merged = {}

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            if not INationalDescriptorAssessment.providedBy(obj):
                continue

            article_title = obj.title
            if article_title != 'Art9-2024':
                continue

            descriptor_folder = obj.aq_parent
            region_folder = descriptor_folder.aq_parent
            country_folder = region_folder.aq_parent

            key = (country_folder.id, region_folder.id, descriptor_folder.id)
            if key in seen:
                continue
            seen.add(key)

            descr_id = descriptor_folder.id.upper()
            country_code = country_folder.id.upper()
            region_code = region_folder.id.upper()

            merge_key = (
                country_code,
                country_folder.title,
                region_code,
                region_folder.title,
                descr_id,
                descriptor_folder.title,
            )

            if merge_key not in merged:
                merged[merge_key] = {'q4': {}, 'q5': {}, 'q6': {}}

            if not (hasattr(obj, 'saved_assessment_data')
                    and obj.saved_assessment_data):
                continue

            data = obj.saved_assessment_data.last()
            q4_score_obj = data.get('Art9-2024_A09Q4_Score')
            q5_score_obj = data.get('Art9-2024_A09Q5_Score')
            q6_score_obj = data.get('Art9-2024_A09Q6_Score')

            if not q4_score_obj or not q6_score_obj:
                continue

            for v_idx in q4_score_obj.values:
                score = q4_score_obj.question.scores[v_idx]
                merged[merge_key]['q4'][score] = \
                    merged[merge_key]['q4'].get(score, 0) + 1

            if q5_score_obj:
                for v_idx in q5_score_obj.values:
                    score = q5_score_obj.question.scores[v_idx]
                    merged[merge_key]['q5'][score] = \
                        merged[merge_key]['q5'].get(score, 0) + 1

            for v_idx in q6_score_obj.values:
                score = q6_score_obj.question.scores[v_idx]
                merged[merge_key]['q6'][score] = \
                    merged[merge_key]['q6'].get(score, 0) + 1

        rows = []
        for (cc, cn, rc, rn, dc, dn), entry in merged.items():
            q4_counts = entry['q4']
            q5_counts = entry['q5']
            q6_counts = entry['q6']
            total_q4 = sum(q4_counts.values()) or 1
            total_q5 = sum(q5_counts.values()) or 1
            total_q6 = sum(q6_counts.values()) or 1

            for score in self.ALL_SCORES:
                q4_cnt = q4_counts.get(score, 0)
                q5_cnt = q5_counts.get(score, 0)
                q6_cnt = q6_counts.get(score, 0)
                rows.append({
                    'country_code': cc,
                    'country_name': cn,
                    'region_code': rc,
                    'region_name': rn,
                    'descriptor_code': self._map_descriptor_code(dc),
                    'descriptor_name': dn,
                    'score': self.SCORE_LABELS.get(score, score),
                    'score_color': self.QUESTION_SCORE_COLORS.get(
                        score, '#eeeeee'),
                    'q4_count': q4_cnt,
                    'q5_count': q5_cnt,
                    'q6_count': q6_cnt,
                    'q4_percentage': round(q4_cnt * 100.0 / total_q4, 1),
                    'q5_percentage': round(q5_cnt * 100.0 / total_q5, 1),
                    'q6_percentage': round(q6_cnt * 100.0 / total_q6, 1),
                })

        def _sort_key(row):
            try:
                desc_idx = self.DESCRIPTOR_ORDER.index(
                    row['descriptor_code'])
            except ValueError:
                desc_idx = 999
            try:
                score_idx = self.SCORE_ORDER.index(row['score'])
            except ValueError:
                score_idx = 999
            return (row['country_code'], row['region_code'],
                    desc_idx, score_idx)

        rows.sort(key=_sort_key)

        output = BytesIO()
        fieldnames = [
            'country_code', 'country_name', 'region_code', 'region_name',
            'descriptor_code', 'descriptor_name',
            'score', 'score_color', 'q4_count', 'q5_count', 'q6_count',
            'q4_percentage', 'q5_percentage', 'q6_percentage',
        ]

        if six.PY2:
            import cStringIO
            text_output = cStringIO.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue())
        else:
            import io
            text_output = io.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue().encode('utf-8'))

        output.seek(0)
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=art9_q4q6_2024.csv'
        )
        return output.read()


class ExportArt9Criteria(AdminScoring):
    """Export Art9-2024 Q1, Q2 and Q4 criteria-level answers as CSV"""

    QUESTION_SCORE_COLORS = {
        '1': '#00b400',
        '0.75': '#96eb96',
        '0.5': '#ffcc99',
        '0.25': '#ff9696',
        '0': '#ff5a5a',
        '0.250': '#b8d1e0',
        '/': '#eeeeee',
    }

    DEFAULT_ANSWER_COLOR = '#eeeeee'

    QUESTIONS = ['A09Q1', 'A09Q2', 'A09Q4',
                 'A08Q1', 'A08Q2', 'A08Q3', 'A08Q4', 'A08Q5', 'A08Q6']

    DESCRIPTOR_ORDER = ['D4', 'D6', 'D1P', 'D3',
                        'D1C', 'D1F', 'D1R', 'D1M', 'D1B',
                        'D11', 'D10', 'D9', 'D8', 'D7', 'D5', 'D2']

    def _get_question(self, question_id, article_title):
        """Return the Art9-2024 definition for a question id"""
        questions = self.questions.get(article_title, [])
        for q in questions:
            if q.id == question_id:
                return q
        return None

    def _normalize_score(self, score):
        """Normalize exported score: Not relevant (/) and 0 -> 0.01"""
        if score in ('/', '0'):
            return '0.01'
        return score

    def _criteria_text(self, element):
        """Criterion title without the trailing parenthetical alternatives"""
        # title = u'{} {}'.format(element.id, element.title)
        title = element.title
        return re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()

    def __call__(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        rows = []
        seen = set()

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            if not INationalDescriptorAssessment.providedBy(obj):
                continue

            article_title = obj.title
            if article_title not in ('Art9-2024', 'Art8-2024'):
                continue

            descriptor_folder = obj.aq_parent
            region_folder = descriptor_folder.aq_parent
            country_folder = region_folder.aq_parent

            descr_id = descriptor_folder.id.upper()
            try:
                descriptor_obj = self.descriptor_obj(descr_id)
            except (KeyError, AttributeError):
                descriptor_obj = None

            data = {}
            if (hasattr(obj, 'saved_assessment_data')
                    and obj.saved_assessment_data):
                last = obj.saved_assessment_data.last()
                if last is not None:
                    data = last

            for question_id in self.QUESTIONS:
                question = self._get_question(question_id, article_title)
                if question is None:
                    continue

                elements = []
                if descriptor_obj is not None:
                    try:
                        elements = question.get_assessed_elements(
                            descriptor_obj)
                    except Exception:
                        elements = []

                for crit_index, element in enumerate(elements):
                    field_name = '{}_{}_{}'.format(
                        question.article, question.id, element.id)
                    value = data.get(field_name, None)

                    answer_score = ''
                    answer_text = ''
                    answer_color = self.DEFAULT_ANSWER_COLOR

                    if value is not None:
                        try:
                            raw_score = question.scores[value]
                            answer_text = question.answers[value]
                            answer_color = self.QUESTION_SCORE_COLORS.get(
                                str(raw_score), self.DEFAULT_ANSWER_COLOR)
                            answer_score = self._normalize_score(raw_score)
                        except (IndexError, KeyError):
                            answer_score = ''
                            answer_text = ''
                            answer_color = self.DEFAULT_ANSWER_COLOR

                    rows.append({
                        'country_code': country_folder.id.upper(),
                        'country_name': country_folder.title,
                        'region_code': region_folder.id.upper(),
                        'region_name': region_folder.title,
                        'descriptor_code': self._map_descriptor_code(descr_id),
                        'descriptor_name': descriptor_folder.title,
                        'question_id': question.id,
                        'criteria': element.id,
                        'criteria_text': self._criteria_text(element),
                        'answer_score': answer_score,
                        'answer_text': answer_text,
                        'answer_color': answer_color,
                        '_question_index': self.QUESTIONS.index(question.id),
                        '_criteria_index': crit_index,
                    })

        def _sort_key(row):
            try:
                desc_idx = self.DESCRIPTOR_ORDER.index(
                    row['descriptor_code'])
            except ValueError:
                desc_idx = 999
            return (row['country_code'], row['region_code'],
                    row['_question_index'], desc_idx, row['_criteria_index'])

        rows.sort(key=_sort_key)

        for row in rows:
            row.pop('_question_index', None)
            row.pop('_criteria_index', None)

        output = BytesIO()
        fieldnames = [
            'country_code', 'country_name', 'region_code', 'region_name',
            'descriptor_code', 'descriptor_name', 'question_id', 'criteria',
            'criteria_text', 'answer_score', 'answer_text', 'answer_color',
        ]

        if six.PY2:
            import cStringIO
            text_output = cStringIO.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue())
        else:
            import io
            text_output = io.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue().encode('utf-8'))

        output.seek(0)
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=art9_criteria_2024.csv'
        )
        return output.read()


class ExportSummary2024CSV(AdminScoring):
    """ExportSummary2024CSV - Summary score data for 2024 articles"""

    csv_filename = 'summary_2024.csv'

    SCORE_COLORS = {
        0: '#eeeeee',
        1: '#00b400',
        2: '#96eb96',
        3: '#ff5a5a',
        4: '#ffcc99',
        5: '#ff9696',
        6: '#b8d1e0',
    }

    DESCRIPTOR_ORDER_2024 = ['D1B', 'D1M', 'D1R', 'D1F', 'D1C', 'D1P',
                             'D4', 'D6', 'D5', 'D8', 'D9', 'D10', 'D11',
                             'D2', 'D3', 'D7']

    def _overall_score_with_coherence(self, obj, weights):
        """Compute overall (conclusion, score) like the assessment overview
        page: phases from the national answers with unanswered phases left
        at max_score 0 (no forcing), coherence from the regional descriptor
        assessment.
        """
        data = obj.saved_assessment_data.last()
        article_title = obj.title
        phase_overall_scores = OverallScores(weights, article_title)
        phase_overall_scores = self._setup_phase_overall_scores(
            phase_overall_scores, data, article_title)
        # _setup_phase_overall_scores forces max_score = 100 for phases with
        # no answered national questions (e.g. consistency for Art9-2024 has
        # no questions); the overview page leaves such phases at 0, so undo
        # the forcing (coherence is overridden below with the regional data)
        answered = set(
            score.question.klass
            for k, score in data.items()
            if '_Score' in k and score)
        for phase in phase_overall_scores.article_weights[article_title]:
            if phase not in answered and phase != 'coherence':
                getattr(phase_overall_scores, phase)['max_score'] = 0
        # coherence comes from the regional descriptor assessment, same as
        # the assessment overview page
        descriptor_folder = obj.aq_parent
        region_folder = descriptor_folder.aq_parent
        phase_overall_scores.coherence = self.get_coherence_data(
            region_folder.id, descriptor_folder.id.upper(), article_title)
        return phase_overall_scores.get_overall_score(article_title)

    def _get_overall_score(self, obj):
        """Compute overall score for an assessment object"""
        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):
            return None, None
        return self._overall_score_with_coherence(obj, ARTICLE_WEIGHTS)

    def _get_color_hex(self, overall_concl):
        """Convert overall_concl to hex color"""
        if overall_concl is None:
            return '#eeeeee'
        color_index = CONCLUSION_COLOR_TABLE.get(overall_concl, 0)
        return self.SCORE_COLORS.get(color_index, '#eeeeee')

    def _format_score(self, overall_concl):
        """Format score as label only"""
        if overall_concl is None:
            return ''
        return self.get_conclusion(overall_concl)

    def __call__(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        entries = []

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            if not INationalDescriptorAssessment.providedBy(obj):
                continue
            if obj.title != 'Art9-2024':
                continue

            descriptor_folder = obj.aq_parent
            region_folder = descriptor_folder.aq_parent
            country_folder = region_folder.aq_parent

            entries.append((
                country_folder.id.upper(), country_folder.title,
                region_folder.id.upper(), region_folder.title,
                self._map_descriptor_code(
                    descriptor_folder.id.upper()),
                descriptor_folder.title,
                descriptor_folder,
            ))

        rows = []

        # First pass: collect D1B (D1 - Biodiversity – birds) Art10 scores
        # per (country, region) so each country's D1M/D1R/D1F/D1C/D1P can
        # inherit its own D1B values
        d1b_art10 = {}
        for (cc, cn, rc, rn, dc, dn, dfolder) in sorted(entries):
            if dc != 'D1B':
                continue
            art10_obj = dfolder.get('art10-2024')
            concl, _score = self._get_overall_score(art10_obj)
            d1b_art10[(cc, rc)] = (
                concl, self._get_color_hex(concl))

        for (cc, cn, rc, rn, dc, dn, dfolder) in sorted(entries):
            art9_obj = dfolder.get('art9-2024')
            art8_obj = dfolder.get('art8-2024')
            art10_obj = dfolder.get('art10-2024')

            art9_concl, _score = self._get_overall_score(art9_obj)
            art8_concl, _score = self._get_overall_score(art8_obj)
            art10_concl, _score = self._get_overall_score(art10_obj)

            # D1M, D1R, D1F, D1C, D1P inherit their country's D1B Art10
            # score & color; fall back to their own values if no D1B exists
            if dc in ('D1M', 'D1R', 'D1F', 'D1C', 'D1P'):
                d1b = d1b_art10.get((cc, rc))
                if d1b is not None:
                    art10_concl, art10_color = d1b
                else:
                    art10_color = self._get_color_hex(art10_concl)
            else:
                art10_color = self._get_color_hex(art10_concl)

            rows.append({
                'Descriptors': dn,
                '_desc_code': dc,
                'Article 9 - GES Determination': self._format_score(art9_concl),
                'Article 8 - Initial Assessment': self._format_score(art8_concl),
                'Article 10 - Environmental Targets': self._format_score(art10_concl),
                'desc_color': '#eeeeee',
                'art9_color': self._get_color_hex(art9_concl),
                'art8_color': self._get_color_hex(art8_concl),
                'art10_color': art10_color,
                'headers': '',
                'country_code': cc,
                'region': rc,
            })

        def _sort_key(row):
            try:
                desc_idx = self.DESCRIPTOR_ORDER_2024.index(
                    row['_desc_code'])
            except ValueError:
                desc_idx = 999
            return (row['country_code'], desc_idx, row['region'])

        rows.sort(key=_sort_key)

        for row in rows:
            row.pop('_desc_code', None)

        first_country = rows[0]['country_code'] if rows else None
        header_labels = ['Article 9', 'Article 8', 'Article 10']
        header_count = 0

        for row in rows:
            if row['country_code'] == first_country:
                if 1 <= header_count <= 3:
                    row['headers'] = header_labels[header_count - 1]
                header_count += 1

        output = BytesIO()
        fieldnames = [
            'Descriptors', 'Article 9 - GES Determination',
            'Article 8 - Initial Assessment',
            'Article 10 - Environmental Targets',
            'desc_color', 'art9_color', 'art8_color', 'art10_color',
            'headers', 'country_code', 'region',
        ]

        if six.PY2:
            import cStringIO
            text_output = cStringIO.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue())
        else:
            import io
            text_output = io.StringIO()
            writer = csv.DictWriter(text_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            output.write(text_output.getvalue().encode('utf-8'))

        output.seek(0)
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename={}'.format(self.csv_filename)
        )
        return output.read()


class ExportSummary2024NoCoherenceCSV(ExportSummary2024CSV):
    """ExportSummary2024NoCoherenceCSV - Same as ExportSummary2024CSV but overall
    scores exclude the 2024 coherence score and use custom article weights:

    - Art9-2024:  completeness * 0.5 + adequacy * 0.5
    - Art8-2024:  completeness * 0.4 + adequacy * 0.4 + consistency * 0.2
    - Art10-2024: adequacy * 0.7 + consistency * 0.3
    """

    csv_filename = 'summary_2024_no_coherence.csv'

    NO_COHERENCE_ARTICLE_WEIGHTS = {
        'Art9-2024': {
            'completeness': 0.5,
            'adequacy': 0.5,
            'consistency': 0.0,
            'coherence': 0.0,
        },
        'Art8-2024': {
            'completeness': 0.4,
            'adequacy': 0.4,
            'consistency': 0.2,
            'coherence': 0.0,
        },
        'Art10-2024': {
            'completeness': 0.0,
            'adequacy': 0.7,
            'consistency': 0.3,
            'coherence': 0.0,
        },
    }

    def _get_overall_score(self, obj):
        """Compute overall score for an assessment object, excluding coherence
        and using the custom article weights above.
        """
        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):
            return None, None

        weights = dict(ARTICLE_WEIGHTS)
        weights.update(self.NO_COHERENCE_ARTICLE_WEIGHTS)

        return self._overall_score_with_coherence(obj, weights)
