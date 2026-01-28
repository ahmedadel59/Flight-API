from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import AND
from datetime import datetime


class FlightPortal(CustomerPortal):

    def _is_admin_user(self):
        return request.env.user.has_group('base.group_system') or request.env.user.has_group('base.group_erp_manager')

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        domain = self._get_flight_domain()
        flight_count = request.env['flight.schedule'].sudo(
        ).search_count(domain)
        values['flight_count'] = flight_count
        return values

    def _get_flight_domain(self):
        if self._is_admin_user():
            return []
        return [('user_id', '=', request.env.user.id)]

    def _check_flight_access(self, flight):
        if not flight.exists():
            return False
        if self._is_admin_user():
            return True
        return flight.user_id.id == request.env.user.id

    @http.route(['/my/flights', '/my/flights/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_flights(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        FlightSchedule = request.env['flight.schedule'].sudo()

        domain = self._get_flight_domain()

        if search and search_in:
            search_domain = []
            if search_in in ('all', 'flight'):
                search_domain = [('flight_number', 'ilike', search)]
            if search_in in ('all', 'origin'):
                search_domain = [('origin', 'ilike', search)] if not search_domain else [
                    '|'] + search_domain + [('origin', 'ilike', search)]
            if search_in in ('all', 'destination'):
                search_domain = [('destination', 'ilike', search)] if not search_domain else [
                    '|'] + search_domain + [('destination', 'ilike', search)]
            domain = AND([domain, search_domain])

        flight_count = FlightSchedule.search_count(domain)

        pager = portal_pager(
            url='/my/flights',
            url_args={'sortby': sortby, 'filterby': filterby,
                      'search_in': search_in, 'search': search},
            total=flight_count,
            page=page,
            step=20,
        )

        flights = FlightSchedule.search(
            domain, limit=50, offset=pager['offset'])

        api_key_configured = bool(request.env['ir.config_parameter'].sudo(
        ).get_param('aviationstack.api_key', ''))

        values = {
            'flights': flights,
            'page_name': 'flights',
            'pager': pager,
            'default_url': '/my/flights',
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'api_key_configured': api_key_configured,
        }

        return request.render('Flight_Task.portal_my_flights', values)

    @http.route(['/my/flights/<int:flight_id>'], type='http', auth='user', website=True)
    def portal_flight_detail(self, flight_id, **kw):
        flight = request.env['flight.schedule'].sudo().browse(flight_id)

        if not self._check_flight_access(flight):
            return request.redirect('/my/flights')

        values = {
            'flight': flight,
            'page_name': 'flight',
        }

        return request.render('Flight_Task.portal_flight_detail', values)

    @http.route('/my/flights/create', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_flight_create(self, **post):
        if request.httprequest.method == 'POST':
            departure_time = False
            arrival_time = False

            if post.get('departure_time'):
                departure_time = datetime.strptime(
                    post.get('departure_time'), '%Y-%m-%dT%H:%M')

            if post.get('arrival_time'):
                arrival_time = datetime.strptime(
                    post.get('arrival_time'), '%Y-%m-%dT%H:%M')

            request.env['flight.schedule'].sudo().create({
                'flight_number': post.get('flight_number'),
                'origin': post.get('origin'),
                'destination': post.get('destination'),
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'price': float(post.get('price') or 0),
                'status': post.get('status', 'active'),
                'is_from_api': False,
                'user_id': request.env.user.id,
            })

            return request.redirect('/my/flights')

        values = {
            'page_name': 'flight_create',
        }
        return request.render('Flight_Task.portal_flight_create', values)

    @http.route('/my/flights/<int:flight_id>/edit', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_flight_edit(self, flight_id, **post):
        flight = request.env['flight.schedule'].sudo().browse(flight_id)

        if not self._check_flight_access(flight):
            return request.redirect('/my/flights')

        if request.httprequest.method == 'POST':
            vals = {}

            if post.get('departure_time'):
                vals['departure_time'] = datetime.strptime(
                    post.get('departure_time'), '%Y-%m-%dT%H:%M')

            if post.get('arrival_time'):
                vals['arrival_time'] = datetime.strptime(
                    post.get('arrival_time'), '%Y-%m-%dT%H:%M')

            if post.get('price'):
                vals['price'] = float(post.get('price', 0))

            if post.get('status'):
                vals['status'] = post.get('status')

            if post.get('origin'):
                vals['origin'] = post.get('origin')

            if post.get('destination'):
                vals['destination'] = post.get('destination')

            if vals:
                flight.write(vals)

            return request.redirect(f'/my/flights/{flight_id}')

        values = {
            'flight': flight,
            'page_name': 'flight_edit',
        }
        return request.render('Flight_Task.portal_flight_edit', values)

    @http.route('/my/flights/<int:flight_id>/delete', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_flight_delete(self, flight_id, **post):

        flight = request.env['flight.schedule'].sudo().browse(flight_id)

        if self._check_flight_access(flight):
            flight.unlink()

        return request.redirect('/my/flights')

    @http.route('/my/flights/sync', type='json', auth='user', methods=['POST'])
    def sync_flights(self, flight_type='realtime', **kwargs):
        api_service = request.env['aviationstack.api'].sudo()
        result = api_service.with_context(
            current_user_id=request.env.user.id).sync_flights_from_api(flight_type=flight_type)
        return result

    @http.route('/my/flights/set-api-key', type='json', auth='user', methods=['POST'])
    def set_api_key(self, api_key='', **kwargs):
        if api_key:
            request.env['ir.config_parameter'].sudo().set_param(
                'aviationstack.api_key', api_key)
            return {'success': True, 'message': 'API key saved successfully'}
        return {'success': False, 'message': 'API key cannot be empty'}
