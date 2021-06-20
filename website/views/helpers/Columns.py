from typing import Callable, Optional
from datetime import datetime

from django.db.models import Min, Max
from django.template import Context, Template

from website.models import Genome, TaxID
from website.views.helpers.extract_requests import extract_data, extract_data_or


def minmax(field: str, is_date=False) -> Callable:
    def minmax_():
        start, end = list(Genome.objects.aggregate(Min(field), Max(field)).values())
        if start is None or end is None or start == end:
            return [None, None]
        if is_date:
            start, end = start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
        return [start, end]

    return minmax_


class Column:
    query = None
    sorted = None

    def __init__(self, label: str, lookup_expr: str = None, id: str = None, annotate_queryset_fn: Optional[Callable] = None):
        self.label = label
        self.id = id if id else label.lower().replace(' ', '_').replace('#', 'nr').replace(':', '')
        self.lookup_expr = lookup_expr if lookup_expr else self.id
        self.annotate_queryset = annotate_queryset_fn

    def __repr__(self):
        return f'<{type(self).__name__}: {self.label}>'

    def filter(self, qs, request):
        raise NotImplementedError(f'function "filter" not implemented: {self}')

    def sort(self, qs, asc: bool):
        asc_desc_prefix = '' if asc else '-'
        qs = qs.order_by(asc_desc_prefix + self.lookup_expr)
        self.sorted = 'asc' if asc else 'desc'
        return qs

    @classmethod
    def html_class(cls):
        return 'ogb-filter-' + cls.__name__.removesuffix('Column').lower()

    def html(self):
        raise NotImplementedError(f'function "html" not implemented: {self}')

    @classmethod
    def activate_js(cls):
        return ''

    @classmethod
    def submit_js(cls):
        return ''


class SimpleColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, qs, request):
        self.query = extract_data_or(request=request, key=self.id)
        if self.query:
            qs = qs.filter(**{self.lookup_expr + '__regex': self.query})
        return qs

    def html(self):
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <input name="{{ self.id }}" type="text" class="form-control" id="id_{{ self.id }}" value="{% if self.query %}{{ self.query }}{% endif %}">
        </div>''').render(Context({'self': self}))


class BinaryColumn(Column):
    def __init__(self, *args, choices: list, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def filter(self, qs, request):
        self.query = extract_data_or(request=request, key=self.id)
        if self.query:
            assert self.query in ['True', 'False']
            query = (self.query == 'True')
            if self.lookup_expr.endswith('__isnull'):
                query = not query
            qs = qs.filter(**{self.lookup_expr: query})
        return qs

    def html(self):
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <select name="{{ self.id }}" class="custom-select" id="id_{{ self.id }}">{% for choice, verbose in self.choices %}
                <option value="{{ choice }}" {% if choice == self.query %} selected{% endif %}>{{ verbose }}</option>{% endfor %}
            </select>
        </div>''').render(Context({'self': self}))


class TagColumn(Column):
    def __init__(self, *args, choices: Callable, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def filter(self, qs, request):
        self.query = extract_data(request=request, key=self.id, list=True, sep=',')
        qs = qs.filter(**{self.lookup_expr + '__in': self.query})
        return qs

    def html(self):
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <input name="{{ self.id }}" hidden>
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <select class="custom-select" id="id_{{ self.id }}" multiple="multiple">{% for choice, verbose in self.choices %}
                <option value="{{ choice }}" {% if choice in self.query %} selected{% endif %}>{{ verbose }}</option>{% endfor %}
            </select>
        </div>''').render(Context({'self': self}))

    @classmethod
    def activate_js(cls):
        return '''
        $('.{{ class }}').each(function(){
            const select = $(this).find('select').first()
            const input = $(this).find('input').first()
            $(select).select2({
                multiple: true
            })
        })'''.replace('{{ class }}', cls.html_class(), 1)

    @classmethod
    def submit_js(cls):
        return '''
        $('.{{ class }}').each(function(){
            const selections = $.map($(this).find(':selected'), e => $(e).val())
            $(this).find('input').first().val(selections.join(','))
        })'''.replace('{{ class }}', cls.html_class(), 1)


class RangeColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.range = minmax(self.lookup_expr, is_date=False)

    def filter(self, qs, request):
        query = extract_data(request=request, key=self.id)
        try:
            start, end = query.split('-', 1)
            start, end = int(start), int(end)
            self.query = [start, end]
        except Exception:
            raise ValueError(f'Error in filter: {self}: Cannot convert into range: {query=}')
        qs = qs.filter(**{self.lookup_expr + '__gte': start, self.lookup_expr + '__lte': end})
        return qs

    def html(self):
        range_start, range_end = self.range()
        query_start, query_end = self.query if self.query else ('', '')
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <input name="{{ self.id }}" hidden>
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <div class="form-control range-container d-flex align-items-center">
                <div class="range-slider" 
                    data-range-start="{{ range_start }}" data-range-end="{{ range_end }}" 
                    data-query-start="{{ query_start }}" data-query-end="{{ query_end }}">
                </div>
            </div>
            <div class="input-group-append">
                <span class="input-group-text range-show"></span>
            </div>
        </div>''').render(
            Context({'self': self, 'range_start': range_start, 'range_end': range_end, 'query_start': query_start, 'query_end': query_end})
        )

    @classmethod
    def activate_js(cls):
        return '''
        $('.{{ class }}').each(function(){
            const rangeSlider = $(this).find('.range-slider')
            const rangeShow = $(this).find('.range-show')
            const input = $(this).find('input').first()
        
            const rangeStart = rangeSlider.data('range-start')
            const rangeEnd = rangeSlider.data('range-end')
            const queryStart = rangeSlider.data('query-start') || rangeStart
            const queryEnd = rangeSlider.data('query-end') || rangeEnd
        
            rangeShow.text(`${queryStart}-${queryEnd}`)
        
            $(rangeSlider).slider({
                range: true, min: rangeStart, max: rangeEnd, values: [queryStart, queryEnd],
                slide: function (event, ui) {
                    const newStart = ui.values[0]
                    const newEnd = ui.values[1]
                    const newString = `${newStart}-${newEnd}`
                    if (rangeStart === newStart && rangeEnd === newEnd) {
                        $(input).val('')
                    } else {
                        $(input).val(newString)
                    }
                    $(rangeShow).text(newString)
                }
            })
        })'''.replace('{{ class }}', cls.html_class(), 1)


class PercentageRangeColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.range = minmax(self.lookup_expr, is_date=False)

    def filter(self, qs, request):
        query = extract_data(request=request, key=self.id)
        try:
            start, end = query.split('-', 1)
            start, end = float(start), float(end)
            self.query = [start, end]
        except Exception:
            raise ValueError(f'Error in filter: {self}: Cannot convert into range: {query=}')
        qs = qs.filter(**{self.lookup_expr + '__gte': start, self.lookup_expr + '__lte': end})
        return qs

    def html(self):
        range_start, range_end = self.range()
        query_start, query_end = self.query if self.query else ('', '')
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <input name="{{ self.id }}" hidden>
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <div class="form-control range-container d-flex align-items-center">
                <div class="range-slider" 
                    data-query-start="{{ query_start }}" data-query-end="{{ query_end }}">
                </div>
            </div>
            <div class="input-group-append">
                <span class="input-group-text range-show"></span>
            </div>
        </div>''').render(
            Context({'self': self, 'range_start': range_start, 'range_end': range_end, 'query_start': query_start, 'query_end': query_end}))

    @classmethod
    def activate_js(cls):
        return '''
        $('.ogb-filter-percentagerange').each(function(){
            const rangeSlider = $(this).find('.range-slider')
            const rangeShow = $(this).find('.range-show')
            const input = $(this).find('input').first()
        
            const queryStart = rangeSlider.data('query-start') || 0
            const queryEnd = rangeSlider.data('query-end') || 1000
        
            rangeShow.text(`${queryStart/10}-${queryEnd/10}`)
        
            $(rangeSlider).slider({
                range: true, min: 0, max: 1000, values: [queryStart * 10, queryEnd * 10],
                slide: function (event, ui) {
                    const newStart = ui.values[0] / 10
                    const newEnd = ui.values[1] / 10
                    const newString = `${newStart}-${newEnd}`
                    if (0 === newStart && 100 === newEnd) {
                        $(input).val('')
                    } else {
                        $(input).val(newString)
                    }
                    $(rangeShow).text(newString)
                }
            })
        })'''.replace('{{ class }}', cls.html_class(), 1)


class DateRangeColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.range = minmax(self.lookup_expr, is_date=True)

    def filter(self, qs, request):
        query = extract_data(request=request, key=self.id)
        try:
            start, end = query.split(':', 1)
            start, end = datetime.strptime(start, '%Y-%m-%d'), datetime.strptime(end, '%Y-%m-%d')
            self.query = [start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')]
        except Exception:
            raise ValueError(f'Error in filter: {self}: Cannot convert into range: {query=}')
        qs = qs.filter(**{self.lookup_expr + '__gte': start, self.lookup_expr + '__lte': end})
        return qs

    def html(self):
        range_start, range_end = self.range()
        query_start, query_end = self.query if self.query else (range_start, range_end)
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <input name="{{ self.id }}" hidden>
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>
            <div id="id_{{ self.id }}" class="date-container form-control d-flex align-items-center justify-content-around">
                <label style="margin:0">from:
                    <input type="date" class="date-from"
                       value="{{ query_start }}" min="{{ range_start }}" max="{{ range_end }}"></label>
                <label style="margin:0">to:
                    <input type="date" class="date-to" 
                        value="{{ query_end }}" min="{{ range_start }}" max="{{ range_end }}"></label>
            </div>
        </div>''').render(
            Context({'self': self, 'range_start': range_start, 'range_end': range_end, 'query_start': query_start, 'query_end': query_end}))

    @classmethod
    def submit_js(cls):
        return '''
        $('.{{ class }}').each(function(){
            const input = $(this).find('input').first()
            const rangeStart = $(this).find('.date-from').attr('min')
            const rangeEnd = $(this).find('.date-from').attr('max')
            const dateStart = $(this).find('.date-from').val() || rangeStart
            const dateEnd = $(this).find('.date-to').val() || rangeEnd
            const value = (rangeStart===dateStart&&rangeEnd===dateEnd) ? '' : `${dateStart}:${dateEnd}`
            console.log('asdfasdfasdfasdfasfd', value)
            input.val(value)
        })'''.replace('{{ class }}', cls.html_class(), 1)


class TaxColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def choices(self):
        if self.id == 'taxonomy':
            return [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(organism__isnull=False).all()]
        if self.id == 'taxid':
            return [(t.id, f'{t.id} ({t.taxscientificname})') for t in TaxID.objects.filter(organism__isnull=False).all()]
        else:
            rank = self.id.removeprefix('tax')
            return [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank=rank).all()]

    def filter(self, qs, request):
        self.query = extract_data(request=request, key=self.id, list=True, sep=',')
        if self.id == 'taxid':
            self.query = [int(t) for t in self.query]
            qs = qs.filter(**{f'organism__taxid__id__in': self.query})
        else:
            qs = qs.filter(**{f'{self.lookup_expr}__in': self.query})
        return qs

    def html(self):
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>    
            <select name="{{ self.id }}" class="custom-select" id="id_{{ self.id }}" multiple="multiple">
                <option value="" {% if not self.query %}selected{% endif %}>--------</option>{% for choice, verbose in self.choices %}
                <option value="{{ choice }}" {% if choice in self.query %} selected{% endif %}>{{ verbose }}</option>{% endfor %}
            </select>
        </div>''').render(Context({'self': self}))

    @classmethod
    def activate_js(cls):
        return '''
        $('.{{ class }} select').each(function(){
            $(this).select2({multiple: false})
        })'''.replace('{{ class }}', cls.html_class(), 1)


class ListColumn(Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def filter(self, qs, request):
        self.query = extract_data(request=request, key=self.id)
        if self.id == 'literature_references':
            qs = qs.filter(**{f'{self.lookup_expr}__contains': [{'name': self.query}]})
        else:
            qs = qs.filter(**{f'{self.lookup_expr}__contains': self.query})
        return qs

    def choices(self):
        if self.id == 'literature_references':
            return set((lr['name'], lr['name']) for lrs in Genome.objects.values_list(self.lookup_expr, flat=True).distinct() for lr in lrs)
        else:
            return set((e, e) for es in Genome.objects.values_list(self.lookup_expr, flat=True).distinct() for e in es)

    def html(self):
        return Template('''
        <div class="input-group mb-3 {{ self.html_class }}" id="form_{{ self.id }}">
            <div class="input-group-prepend">
                <label class="input-group-text" for="id_{{ self.id }}">{{ self.label }}</label>
            </div>    
            <select name="{{ self.id }}" class="custom-select" id="id_{{ self.id }}">
                <option value="" {% if not self.query %}selected{% endif %}>--------</option>{% for choice, verbose in self.choices %}
                <option value="{{ choice }}" {% if choice == self.query %} selected{% endif %}>{{ verbose }}</option>{% endfor %}
            </select>
        </div>''').render(Context({'self': self}))

    @classmethod
    def activate_js(cls):
        return '''
        $('.{{ class }} select').each(function(){
            $(this).select2({multiple: false})
        })'''.replace('{{ class }}', cls.html_class(), 1)
