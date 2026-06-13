from sqlalchemy import text, bindparam


class CarEtlRepository:
    def get_active_car_ids(self, db, limit: int = 100, offset: int = 0):
        query = text("""
            SELECT c.car_id
            FROM cars c
            WHERE c.is_active = TRUE
              AND c.deleted_at IS NULL
            ORDER BY c.car_id ASC
            LIMIT :limit OFFSET :offset
        """)
        return db.execute(query, {"limit": limit, "offset": offset}).scalars().all()

    def get_car_main(self, db, car_id: int):
        query = text("""
            SELECT
                c.car_id,
                c.car_name,
                CONCAT('cars/', b.slug, '/', m.slug) AS url,
                c.is_popular,
                c.is_trending,
                c.is_ev,
                c.description,
                c.year,
                c.launched_at,
                c.discontinued_at,
                c.overview,
                c.latest_updates,
                c.engine_and_performance,
                c.fuel_economy,
                c.interior,
                c.exterior,
                c.safety,
                c.competition,
                c.final_verdict,
                c.pricing_and_features,
                c.buying_advice,
                c.latest_offers,
                c.faq_data,
                c.overall,
                c.pros,
                c.cons,
                c.whats_new,
                c.overall_rating,
                c.brochure,
                c.is_best_sell,
                c.is_upcoming,
                c.upcoming_date,
                c.upcoming_type,
                c.upcoming_updates,
                c.is_discontinued,
                c.new_car_id,
                c.key_highlights,
                c.gst_reform_price,
                c.is_gst_reform,

                b.brand_id,
                b.name AS brand_name,
                b.slug AS brand_slug,

                m.model_id,
                m.name AS model_name,
                m.slug AS model_slug,

                sm.submodel_id,
                sm.submodel_name,
                sm.submodel_slug,

                tr.min_price,
                tr.max_price,
                tr.min_engine_displacement,
                tr.max_engine_displacement,
                tr.min_mileage,
                tr.max_mileage,
                tr.min_no_of_airbags,
                tr.max_no_of_airbags,
                tr.seat_capacities,
                tr.transmissions,
                tr.fuel_types
            FROM cars c
            INNER JOIN brands b
                ON c.brand_id = b.brand_id
               AND b.is_active = TRUE
               AND b.deleted_at IS NULL
            INNER JOIN models m
                ON c.model_id = m.model_id
               AND m.is_active = TRUE
            LEFT JOIN submodels sm
                ON c.submodel_id = sm.submodel_id
               AND sm.is_active = TRUE
            LEFT JOIN (
                SELECT
                    t.car_id,
                    MIN(t.absolute_price) AS min_price,
                    MAX(t.absolute_price) AS max_price,
                    MIN(es.displacement) AS min_engine_displacement,
                    MAX(es.displacement) AS max_engine_displacement,
                    MIN(COALESCE(
                        fs.petrol_mileage_arai,
                        fs.cng_mileage_arai,
                        fs.diesel_mileage_arai,
                        fs.electric_mileage_arai,
                        fs.range_tested
                    )) AS min_mileage,
                    MAX(COALESCE(
                        fs.petrol_mileage_arai,
                        fs.cng_mileage_arai,
                        fs.diesel_mileage_arai,
                        fs.electric_mileage_arai,
                        fs.range_tested
                    )) AS max_mileage,
                    MIN(sf.no_of_airbags) AS min_no_of_airbags,
                    MAX(sf.no_of_airbags) AS max_no_of_airbags,
                    COALESCE(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ins.seating_capacity)), ']'), '[]') AS seat_capacities,
                    COALESCE(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(t.transmission)), ']'), '[]') AS transmissions,
                    COALESCE(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(fs.fuel_type)), ']'), '[]') AS fuel_types
                FROM trims t
                LEFT JOIN trim_engine_spec es
                    ON t.trim_id = es.trim_id
                   AND es.deleted_at IS NULL
                LEFT JOIN trim_fuel_spec fs
                    ON t.trim_id = fs.trim_id
                   AND fs.deleted_at IS NULL
                LEFT JOIN trim_safety_feature sf
                    ON t.trim_id = sf.trim_id
                   AND sf.deleted_at IS NULL
                LEFT JOIN trim_interior_spec ins
                    ON t.trim_id = ins.trim_id
                   AND ins.deleted_at IS NULL
                WHERE t.is_active = TRUE
                  AND t.deleted_at IS NULL
                GROUP BY t.car_id
            ) tr ON c.car_id = tr.car_id
            WHERE c.car_id = :car_id
              AND c.is_active = TRUE
              AND c.deleted_at IS NULL
            LIMIT 1
        """)
        row = db.execute(query, {"car_id": car_id}).mappings().first()
        return dict(row) if row else None

    def get_car_images(self, db, car_id: int):
        query = text("""
            SELECT
                ci.id,
                ci.image_path,
                ci.alt_text,
                ci.image_type,
                ci.color_id,
                col.color_name,
                col.color_code
            FROM car_images ci
            LEFT JOIN colors col
                ON ci.color_id = col.id
               AND col.deleted_at IS NULL
            WHERE ci.car_id = :car_id
              AND ci.is_active = TRUE
            ORDER BY ci.image_type, ci.id
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]

    def get_car_trims(self, db, car_id: int):
        query = text("""
            SELECT
                t.trim_id,
                t.trim_name,
                t.bodystyle,
                t.price,
                t.absolute_price,
                t.transmission,
                t.engine,
                t.configuration,
                t.is_base,
                t.is_top,
                t.is_popular,
                t.discontinued_at,
                t.launched_at,
                t.is_new,
                t.market_active_date,
                t.market_discon_date,
                t.is_discontinued,

                fs.fuel_type,
                fs.petrol_mileage_arai,
                fs.petrol_fuel_tank_capacity,
                fs.emission_norm_compliance,
                fs.fuel_tank_capacity,
                fs.cng_mileage_arai,
                fs.cng_fuel_tank_capacity,
                fs.secondary_fuel_type,
                fs.petrol_fuel_tank_capacity_litres,
                fs.petrol_highway_mileage,
                fs.city_mileage,
                fs.battery_type,
                fs.cng_highway_mileage,
                fs.diesel_mileage_arai,
                fs.diesel_fuel_tank_capacity,
                fs.max_range,
                fs.range_tested,
                fs.diesel_highway_mileage,
                fs.drag_coefficient,
                fs.petrol_mileage_wltp,
                fs.wltp_mileage,
                fs.diesel_mileage_wltp,
                fs.petrol_overall_mileage,
                fs.emission_control_system,
                fs.lpg_mileage_arai,
                fs.lpg_fuel_tank_capacity,
                fs.electric_mileage_arai,

                es.engine_type,
                es.displacement,
                es.max_power,
                es.max_power_short,
                es.max_torque,
                es.max_torque_short,
                es.no_of_cylinders,
                es.valves_per_cylinder,
                es.turbo_charger,
                es.transmission_type,
                es.gearbox,
                es.drive_type,
                es.engine_displacement,
                es.engine_start_stop_button AS engine_spec_start_stop_button,
                es.idle_start_stop_system,
                es.valve_configuration,
                es.top_speed,
                es.fuel_supply_system,
                es.motor_type,
                es.battery_saver,
                es.vehicle_to_vehicle_charging,
                es.vehicle_to_load_charging,
                es.battery_capacity,
                es.motor_power,
                es.charging_time_a_c,
                es.charging_time_d_c,
                es.regenerative_braking,
                es.regenerative_braking_levels,
                es.charging_port,
                es.charging_options,
                es.charger_type,
                es.charging_time_15_a_plug_point,
                es.charging_time_7_2_kw_ac_fast_charger,
                es.charging_time,
                es.fast_charging,
                es.charging_time_50_kw_dc_fast_charger,
                es.hybrid_type,
                es.super_charge,

                ds.length,
                ds.width,
                ds.height,
                ds.ground_clearance,
                ds.ground_clearance_laden,
                ds.ground_clearance_unladen,
                ds.wheelbase,
                ds.kerb_weight,
                ds.gross_weight,
                ds.body_type,

                ins.boot_space,
                ins.seating_capacity,
                ins.boot_space_rear_seat_folding,
                ins.no_of_doors,

                inf.additional_features,
                inf.tachometer,
                inf.leather_wrapped_steering_wheel,
                inf.digital_cluster,
                inf.upholstery,
                inf.dual_tone_dashboard,
                inf.digital_clock,
                inf.fabric_upholstery,
                inf.electronic_multi_tripmeter,
                inf.leather_wrap_gear_shift_selector,
                inf.compass,
                inf.ambient_light_colour_numbers,

                sf.parking_sensors,
                sf.real_time_vehicle_tracking,
                sf.anti_lock_braking_system_abs,
                sf.central_locking,
                sf.anti_theft_alarm,
                sf.no_of_airbags,
                sf.driver_airbag,
                sf.passenger_airbag,
                sf.side_airbag,
                sf.side_airbag_rear,
                sf.day_night_rear_view_mirror,
                sf.curtain_airbag,
                sf.electronic_brakeforce_distribution_ebd,
                sf.seat_belt_warning,
                sf.door_ajar_warning,
                sf.engine_immobilizer,
                sf.electronic_stability_control_esc,
                sf.rear_camera,
                sf.anti_theft_device,
                sf.anti_pinch_power_windows,
                sf.speed_alert,
                sf.speed_sensing_auto_door_lock,
                sf.isofix_child_seat_mounts,
                sf.hill_assist,
                sf.global_ncap_safety_rating,
                sf.360_view_camera,
                sf.tyre_pressure_monitoring_system_tpms,
                sf.global_ncap_child_safety_rating,
                sf.child_safety_locks,
                sf.brake_assist,
                sf.hill_descent_control,
                sf.bharat_ncap_safety_rating,
                sf.bharat_ncap_child_safety_rating,

                wt.wheel_covers,
                wt.alloy_wheels,
                wt.tyre_size,
                wt.tyre_type,
                wt.wheel_size,
                wt.alloy_wheel_size_front,
                wt.alloy_wheel_size_rear,
                wt.front_track,
                wt.rear_track,
                wt.alloy_wheel_size,

                info.voice_commands,
                info.usb_charger,
                info.antenna,
                info.radio,
                info.wireless_phone_charging,
                info.bluetooth_connectivity,
                info.touchscreen,
                info.touchscreen_size,
                info.android_auto,
                info.apple_carplay,
                info.usb_ports,
                info.speakers,
                info.live_location,
                info.over_the_air_ota_updates,
                info.google_alexa_connectivity,
                info.smartwatch_app,
                info.no_of_speakers,
                info.multi_function_steering_wheel,
                info.digital_cluster_size,
                info.navigation_with_live_traffic,
                info.wireless_charging,
                info.navigation_system,

                ps.braking_100_0_kmph,
                ps.zero_100kmph_tested,
                ps.city_driveability_20_80_kmph,
                ps.braking_80_0_kmph,
                ps.paddle_shifters,
                ps.acceleration,
                ps.zero_100kmph,
                ps.braking_60_0_kmph,
                ps.drive_modes,
                ps.drive_mode_types,
                ps.acceleration_0_100kmph,
                ps.acceleration_0_60kmph,
                ps.fourth_gear_40_100_kmph,
                ps.towing_capacity,
                ps.quarter_mile,

                ss.front_suspension,
                ss.rear_suspension,
                ss.steering_type,
                ss.steering_column,
                ss.turning_radius,
                ss.front_brake_type,
                ss.rear_brake_type,
                ss.steering_gear_type,
                ss.approach_angle,
                ss.break_over_angle,
                ss.departure_angle,
                ss.shock_absorbers_type,

                cc.power_steering,
                cc.air_conditioner,
                cc.heater,
                cc.adjustable_steering,
                cc.height_adjustable_driver_seat,
                cc.automatic_climate_control,
                cc.accessory_power_outlet,
                cc.trunk_light,
                cc.vanity_mirror,
                cc.rear_reading_lamp,
                cc.adjustable_headrest,
                cc.rear_ac_vents,
                cc.cruise_control,
                cc.foldable_rear_seat,
                cc.keyless_entry,
                cc.engine_start_stop_button AS comfort_engine_start_stop_button,
                cc.power_windows,
                cc.power_windows_front,
                cc.cooled_glovebox,
                cc.ventilated_seats,
                cc.electric_adjustable_seats,
                cc.remote_trunk_opener,
                cc.remote_fuel_lid_opener,
                cc.low_fuel_warning_light,
                cc.trunk_opener,
                cc.rain_sensing_wiper,
                cc.leather_seats,
                cc.power_boot,
                cc.heated_seats,

                ef.rear_window_wiper,
                ef.rear_window_washer,
                ef.rear_window_defogger,
                ef.rear_spoiler,
                ef.outside_rear_view_mirror_turn_indicators,
                ef.projector_headlamps,
                ef.halogen_headlamps,
                ef.fog_lights,
                ef.sun_roof,
                ef.boot_opening,
                ef.outside_rear_view_mirror_orvm,
                ef.led_drls,
                ef.led_headlamps,
                ef.led_taillights,
                ef.led_fog_lamps,
                ef.chrome_grille,
                ef.roof_rails,
                ef.sunroof,
                ef.headlamp_washers,
                ef.tinted_glass,
                ef.puddle_lamps,
                ef.dual_tone_body_colour,

                wf.service_cost,
                wf.battery_warranty,
                wf.engine_check_warning,
                wf.battery_warranty_years,
                wf.battery_warranty_kilometres,
                wf.warranty_years,
                wf.warranty_kilometres
            FROM trims t
            LEFT JOIN trim_fuel_spec fs ON t.trim_id = fs.trim_id AND fs.deleted_at IS NULL
            LEFT JOIN trim_engine_spec es ON t.trim_id = es.trim_id AND es.deleted_at IS NULL
            LEFT JOIN trim_dimensions_spec ds ON t.trim_id = ds.trim_id AND ds.deleted_at IS NULL
            LEFT JOIN trim_interior_spec ins ON t.trim_id = ins.trim_id AND ins.deleted_at IS NULL
            LEFT JOIN trim_interior_features inf ON t.trim_id = inf.trim_id AND inf.deleted_at IS NULL
            LEFT JOIN trim_safety_feature sf ON t.trim_id = sf.trim_id AND sf.deleted_at IS NULL
            LEFT JOIN trim_wheels_tires_spec wt ON t.trim_id = wt.trim_id AND wt.deleted_at IS NULL
            LEFT JOIN trim_infotainment_feature info ON t.trim_id = info.trim_id AND info.deleted_at IS NULL
            LEFT JOIN trim_performance_spec ps ON t.trim_id = ps.trim_id AND ps.deleted_at IS NULL
            LEFT JOIN trim_suspension_brakes_steering_spec ss ON t.trim_id = ss.trim_id AND ss.deleted_at IS NULL
            LEFT JOIN trim_comfort_convenience_feature cc ON t.trim_id = cc.trim_id AND cc.deleted_at IS NULL
            LEFT JOIN trim_exterior_features ef ON t.trim_id = ef.trim_id AND ef.deleted_at IS NULL
            LEFT JOIN trim_maintenance_warranty_feature wf ON t.trim_id = wf.trim_id AND wf.deleted_at IS NULL
            WHERE t.car_id = :car_id
              AND t.is_active = TRUE
              AND t.deleted_at IS NULL
            ORDER BY t.absolute_price ASC
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]

    def get_trim_city_prices(self, db, trim_ids: list[int]):
        if not trim_ids:
            return []

        query = text("""
            SELECT
                tcp.id,
                tcp.car_id,
                tcp.trim_id,
                tcp.city_id,
                c.city_name,
                c.city_slug,
                c.is_popular AS city_is_popular,
                c.latitude,
                c.longitude,
                c.state_id,
                tcp.ex_showroom_price,
                tcp.ex_showroom_price_abs,
                tcp.rto,
                tcp.rto_absolute,
                tcp.insurance,
                tcp.insurance_absolute,
                tcp.others,
                tcp.others_absolute,
                tcp.optional_accessories,
                tcp.optional_accessories_absolute,
                tcp.on_road_price,
                tcp.on_road_price_absolute
            FROM trims_city_price tcp
            INNER JOIN cities c
                ON tcp.city_id = c.id
               AND c.is_active = TRUE
            WHERE tcp.trim_id IN :trim_ids
              AND tcp.is_active = TRUE
              AND tcp.deleted_at IS NULL
            ORDER BY c.city_name ASC, tcp.on_road_price_absolute ASC
        """).bindparams(bindparam("trim_ids", expanding=True))

        return [dict(row) for row in db.execute(query, {"trim_ids": trim_ids}).mappings().all()]

    def get_standout_features(self, db, car_id: int):
        query = text("""
            SELECT
                id,
                image_path,
                caption
            FROM stand_out_features
            WHERE car_id = :car_id
              AND is_active = TRUE
              AND deleted_at IS NULL
            ORDER BY id ASC
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]

    def get_similar_cars(self, db, car_id: int):
        query = text("""
            SELECT
                sc.id,
                sc.similar_car_id,
                c.car_name AS similar_car_name,
                CONCAT('cars/', b.slug, '/', m.slug) AS similar_car_url,
                c.overall_rating,
                c.is_ev,
                c.is_upcoming,
                c.is_discontinued,
                b.name AS brand_name,
                b.slug AS brand_slug,
                m.name AS model_name,
                m.slug AS model_slug,
                sm.submodel_name,
                sm.submodel_slug
            FROM similar_cars sc
            INNER JOIN cars c
                ON sc.similar_car_id = c.car_id
               AND c.is_active = TRUE
               AND c.deleted_at IS NULL
            LEFT JOIN brands b
                ON c.brand_id = b.brand_id
               AND b.deleted_at IS NULL
            LEFT JOIN models m
                ON c.model_id = m.model_id
            LEFT JOIN submodels sm
                ON c.submodel_id = sm.submodel_id
            WHERE sc.car_id = :car_id
              AND sc.is_active = TRUE
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]

    def get_related_news(self, db, car_id: int):
        query = text("""
            SELECT
                n.id,
                n.title,
                n.excerpt,
                n.description,
                n.url,
                n.hero_image,
                n.likes_count,
                n.major_category,
                n.minor_category,
                n.news_flag,
                n.created_at,
                n.updated_at
            FROM news n
            WHERE n.deleted_at IS NULL
              AND n.is_active = TRUE
              AND JSON_OVERLAPS(n.car_id, JSON_ARRAY(:car_id))
            ORDER BY n.updated_at DESC
            LIMIT 20
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]

    def get_comparisons(self, db, car_id: int):
        query = text("""
            SELECT
                cc.id,
                cc.description,
                cc.is_popular,
                cc.image_path,
                cc.title,
                cc.content,
                cc.car1_summary,
                cc.car2_summary,
                cc.car1_why_choose,
                cc.car2_why_choose,
                cc.car1_recommendation,
                cc.car2_recommendation,

                c1.car_id,
                c1.car_name,
                CONCAT('cars/', b1.slug, '/', m1.slug) AS car_url,
                b1.name AS brand_name,
                b1.slug AS brand_slug,
                m1.name AS model_name,
                m1.slug AS model_slug,
                sm1.submodel_name,
                sm1.submodel_slug,

                c2.car_id AS compare_car_id,
                c2.car_name AS compare_car_name,
                CONCAT('cars/', b2.slug, '/', m2.slug) AS compare_car_url,
                b2.name AS compare_brand_name,
                b2.slug AS compare_brand_slug,
                m2.name AS compare_model_name,
                m2.slug AS compare_model_slug,
                sm2.submodel_name AS compare_submodel_name,
                sm2.submodel_slug AS compare_submodel_slug
            FROM car_compares cc
            INNER JOIN cars c1
                ON cc.car_id = c1.car_id
               AND c1.is_active = TRUE
               AND c1.deleted_at IS NULL
            INNER JOIN cars c2
                ON cc.compare_car_id = c2.car_id
               AND c2.is_active = TRUE
               AND c2.deleted_at IS NULL
            LEFT JOIN brands b1 ON c1.brand_id = b1.brand_id
            LEFT JOIN models m1 ON c1.model_id = m1.model_id
            LEFT JOIN submodels sm1 ON c1.submodel_id = sm1.submodel_id
            LEFT JOIN brands b2 ON c2.brand_id = b2.brand_id
            LEFT JOIN models m2 ON c2.model_id = m2.model_id
            LEFT JOIN submodels sm2 ON c2.submodel_id = sm2.submodel_id
            WHERE cc.car_id = :car_id
              AND cc.is_active = TRUE
              AND cc.deleted_at IS NULL
            ORDER BY cc.priority DESC
            LIMIT 10
        """)
        return [dict(row) for row in db.execute(query, {"car_id": car_id}).mappings().all()]