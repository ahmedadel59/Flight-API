import requests
from odoo import models, fields, api
from datetime import datetime

AVIATIONSTACK_BASE_URL = "http://api.aviationstack.com/v1"


class AviationStackAPI(models.AbstractModel):
    _name = 'aviationstack.api'
    _description = 'AviationStack API Service'

    @api.model
    def get_api_key(self):
        return self.env['ir.config_parameter'].sudo().get_param('aviationstack.api_key', '')

    @api.model
    def fetch_real_time_flights(self, limit=100, flight_status=None, airline_iata=None, dep_iata=None, arr_iata=None):

        api_key = self.get_api_key()
        if not api_key:
            return {'error': 'API key not configured. Please set it in Settings.'}

        params = {
            'access_key': api_key,
            'limit': limit,
        }

        if flight_status:
            params['flight_status'] = flight_status
        if airline_iata:
            params['airline_iata'] = airline_iata
        if dep_iata:
            params['dep_iata'] = dep_iata
        if arr_iata:
            params['arr_iata'] = arr_iata

        response = requests.get(
            f"{AVIATIONSTACK_BASE_URL}/flights", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            return {'error': data['error'].get('message', 'API error occurred')}

        return data

    @api.model
    def fetch_flight_schedules(self, limit=100, iata_code=None, flight_date=None):

        api_key = self.get_api_key()
        if not api_key:
            return {'error': 'API key not configured. Please set it in Settings.'}

        params = {
            'access_key': api_key,
            'limit': limit,
        }

        if iata_code:
            params['iata_code'] = iata_code
        if flight_date:
            params['flight_date'] = flight_date

        response = requests.get(
            f"{AVIATIONSTACK_BASE_URL}/timetable", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            return {'error': data['error'].get('message', 'API error occurred')}

        return data

    @api.model
    def sync_flights_from_api(self, flight_type='both'):

        FlightSchedule = self.env['flight.schedule']
        current_user_id = self.env.context.get(
            'current_user_id') or self.env.user.id

    # 1️⃣ Fetch realtime flights (today)
        if flight_type in ('realtime', 'both'):
            realtime_data = self.fetch_real_time_flights(limit=20)
        if 'error' in realtime_data:
            return {'success': False, 'message': realtime_data['error']}

    # 2️⃣ Fetch scheduled flights (upcoming)
        schedule_data = self.fetch_flight_schedules(limit=20)
        if 'error' in schedule_data:
            return {'success': False, 'message': schedule_data['error']}

    # 3️⃣ Merge both datasets
        flights_data = (
            realtime_data.get('data', []) +
            schedule_data.get('data', [])
        )

        synced_count = 0

        for flight in flights_data:
            flight_number = (
                flight.get('flight', {}).get('iata')
                or flight.get('flight', {}).get('number')
            )
            if not flight_number:
                continue

            existing = FlightSchedule.search([
                ('flight_number', '=', flight_number),
                ('user_id', '=', current_user_id)
            ], limit=1)

            departure_time = False
            arrival_time = False

            dep_scheduled = flight.get('departure', {}).get('scheduled')
            arr_scheduled = flight.get('arrival', {}).get('scheduled')

            if dep_scheduled:
                departure_time = datetime.fromisoformat(
                    dep_scheduled.replace('Z', '+00:00')
                ).replace(tzinfo=None)

            if arr_scheduled:
                arrival_time = datetime.fromisoformat(
                    arr_scheduled.replace('Z', '+00:00')
                ).replace(tzinfo=None)

            flight_status = flight.get('flight_status', 'scheduled')
            status = (
                'cancelled' if flight_status == 'cancelled'
                else 'active'
            )

            vals = {
                'flight_number': flight_number,
                'origin': flight.get('departure', {}).get('airport', ''),
                'destination': flight.get('arrival', {}).get('airport', ''),
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'status': status,
                'airline_name': flight.get('airline', {}).get('name', ''),
                'airline_iata': flight.get('airline', {}).get('iata', ''),
                'departure_iata': flight.get('departure', {}).get('iata', ''),
                'arrival_iata': flight.get('arrival', {}).get('iata', ''),
                'flight_status_api': flight_status,
                'is_from_api': True,
                'user_id': current_user_id,
            }

            if existing:
                existing.write(vals)
            else:
                FlightSchedule.create(vals)

            synced_count += 1

        return {
            'success': True,
            'message': f'Successfully synced {synced_count} flights (Today + Upcoming)'
        }
