#!/usr/bin/env python3
"""
PrusaSlicer config bundle (.ini) → OrcaSlicer printer bundle (.orca_printer) converter
Usage: python convert.py input.ini [-o output.orca_printer]
"""

import json
import zipfile
import sys
import argparse
import datetime
from pathlib import Path

# =================== CONVERSION LOG ===================

class SectionLog:
    """Trace tous les champs d'une section convertie."""

    # Champs internes / méta à ne pas signaler comme ignorés
    _META_KEYS = {
        'compatible_printers', 'compatible_printers_condition',
        'compatible_prints', 'compatible_prints_condition',
        'inherits', 'print_settings_id', 'filament_settings_id',
        'printer_settings_id', 'custom_parameters_print',
        'custom_parameters_filament', 'custom_parameters_printer',
        'printer_model', 'printer_variant', 'printer_vendor',
        'printer_technology', 'host_type', 'print_host',
        'printhost_apikey', 'printhost_cafile', 'printhost_authorization_type',
        'printhost_ssl_ignore_revoke', 'printhost_password', 'printhost_port',
        'printhost_user', 'remaining_times', 'variable_layer_height',
        'single_extruder_multi_material', 'single_extruder_multi_material_priming',
        'idle_temperature', 'filament_settings_id',
        # Slicing-only internals with no Orca equivalent
        'support_material_solid_first_layer', 'support_material_synchronize_layers',
        'support_material_with_sheath', 'clip_multipart_objects',
        'no_perimeter_unsupported_algo', 'infill_only_where_needed',
        'solid_infill_below_area', 'solid_infill_every_layers',
        'infill_every_layers', 'perimeter_extruder',
        'infill_extruder', 'solid_infill_extruder',
        'support_material_extruder', 'support_material_interface_extruder',
        'mmu_segmented_region_max_width', 'wipe_advanced',
        'wipe_advanced_algo', 'wipe_advanced_multiplier',
        'wipe_advanced_nozzle_melted_volume', 'filament_ramming_parameters',
        'filament_wipe_advanced_pigmented', 'between_objects_gcode',
        'default_filament_profile', 'default_print_profile',
        'machine_limits_usage', 'bed_custom_model', 'bed_custom_texture',
        'first_layer_min_speed', 'max_print_speed',
        # PrusaSlicer-specific features without Orca equivalent
        'interlocking_beam', 'interlocking_beam_layer_count', 'interlocking_beam_width',
        'interlocking_boundary_avoidance', 'interlocking_depth', 'interlocking_orientation',
        'scarf_seam_entire_loop', 'scarf_seam_length', 'scarf_seam_max_segment_length',
        'scarf_seam_on_inner_perimeters', 'scarf_seam_only_on_smooth',
        'scarf_seam_placement', 'scarf_seam_start_height',
        'support_tree_angle_slow', 'support_tree_branch_diameter_angle',
        'support_tree_branch_diameter_double_wall', 'support_tree_branch_distance',
        'support_tree_top_rate', 'support_material_closing_radius',
        'support_material_enforce_layers', 'support_material_interface_pattern',
        'wipe_tower_extra_flow', 'wipe_tower_extra_spacing', 'wipe_tower_cone_angle',
        'wipe_tower_acceleration', 'wipe_tower_extruder',
        'first_layer_speed_over_raft', 'first_layer_acceleration_over_raft',
        'automatic_extrusion_widths', 'automatic_infill_combination',
        'automatic_infill_combination_max_layer_height',
        'avoid_crossing_curled_overhangs', 'enable_dynamic_overhang_speeds',
        'slice_closing_radius', 'top_one_perimeter_type', 'extra_perimeters',
        'infill_first', 'ooze_prevention', 'only_one_perimeter_first_layer',
        'max_volumetric_extrusion_rate_slope_negative', 'max_volumetric_extrusion_rate_slope_positive',
        'travel_short_distance_acceleration', 'mmu_segmented_region_interlocking_depth',
        'post_process', 'gcode_substitutions',
        # Filament fields without Orca equivalent
        'cooling', 'cooling_slowdown_logic', 'cooling_perimeter_transition_distance',
        'enable_dynamic_fan_speeds', 'fan_always_on',
        'filament_multitool_ramming_volume', 'filament_purge_multiplier',
        'filament_shrinkage_compensation_xy', 'filament_shrinkage_compensation_z',
        'filament_spool_weight', 'filament_abrasive',
        'filament_infill_max_crossing_speed', 'filament_infill_max_speed',
        'filament_travel_lift_before_obstacle', 'filament_travel_max_lift',
        'filament_travel_ramping_lift', 'filament_travel_slope',
        'filament_seam_gap_distance', 'filament_retract_length_toolchange',
        'filament_retract_restart_extra_toolchange',
        # Overhang fan zones 1-3 (Orca only has one speed+threshold)
        'overhang_fan_speed_1', 'overhang_fan_speed_2', 'overhang_fan_speed_3',
    }

    def __init__(self, name, section_type):
        self.name         = name
        self.type         = section_type   # 'printer' | 'filament' | 'process'
        self.mapped       = []   # (prusa_key, orca_key, value, note, is_approx)
        self.skipped      = []   # (prusa_key, value)
        self._consumed    = set()

    def log(self, prusa_key, orca_key, value, note='', approx=False):
        self._consumed.add(prusa_key)
        self.mapped.append((prusa_key, orca_key, str(value)[:80], note, approx))

    def finalize(self, source_data):
        """Détecte les clés non converties."""
        for k, v in source_data.items():
            if k in self._consumed or k in self._META_KEYS:
                continue
            # Ignore les valeurs vides / nil / zéro sans intérêt
            if v in ('', 'nil', None, '0', '""'):
                continue
            # Ignore les pourcentages nuls comme "0%"
            if isinstance(v, str) and v.rstrip('%') == '0':
                continue
            self.skipped.append((k, str(v)[:80]))

    @property
    def n_mapped(self):   return len(self.mapped)
    @property
    def n_skipped(self):  return len(self.skipped)
    @property
    def n_approx(self):   return sum(1 for *_, a in self.mapped if a)


class ConversionLog:
    """Conteneur global du rapport de conversion."""

    def __init__(self):
        self.sections  = []     # list[SectionLog]
        self.warnings  = []     # list[str]

    def new_section(self, name, section_type):
        sl = SectionLog(name, section_type)
        self.sections.append(sl)
        return sl

    def warn(self, msg):
        self.warnings.append(msg)

    @property
    def total_mapped(self):  return sum(s.n_mapped  for s in self.sections)
    @property
    def total_skipped(self): return sum(s.n_skipped for s in self.sections)
    @property
    def total_approx(self):  return sum(s.n_approx  for s in self.sections)


# =================== VALUE MAPPINGS ===================

FILL_PATTERN_MAP = {
    'rectilinear': 'rectilinear',
    'alignedrectilinear': 'alignedrectilinear',
    'grid': 'grid',
    'triangles': 'triangles',
    'stars': 'stars',
    'cubic': 'cubic',
    'line': 'line',
    'concentric': 'concentric',
    'honeycomb': 'honeycomb',
    '3dhoneycomb': '3dhoneycomb',
    'gyroid': 'gyroid',
    'hilbertcurve': 'hilbertcurve',
    'archimedeanchords': 'archimedeanchords',
    'octagramspiral': 'octagramspiral',
    'supportcubic': 'supportcubic',
    'lightning': 'lightning',
}

SURFACE_PATTERN_MAP = {
    'monotonic': 'monotonic',
    'monotoniclines': 'monotonicline',
    'alignedrectilinear': 'alignedrectilinear',
    'concentric': 'concentric',
    'hilbertcurve': 'hilbertcurve',
    'archimedeanchords': 'archimedeanchords',
    'octagramspiral': 'octagramspiral',
    'rectilinear': 'rectilinear',
}

SEAM_POSITION_MAP = {
    'aligned': ('aligned', False),
    'rear':    ('back',    False),
    'nearest': ('nearest', False),
    'random':  ('random',  False),
    'contiguous': ('nearest', True),   # approx
}

BRIM_TYPE_MAP = {
    'outer_only':     'outer_only',
    'inner_only':     'inner_only',
    'outer_and_inner':'outer_and_inner',
    'no_brim':        'no_brim',
}

GCODE_FLAVOR_MAP = {
    'reprap': 'reprap', 'reprapfirmware': 'reprapfirmware',
    'marlin': 'marlin', 'marlin2': 'marlin2', 'klipper': 'klipper',
    'repetier': 'repetier', 'teacup': 'teacup', 'sprinter': 'sprinter',
    'mach3': 'mach3', 'machinekit': 'machinekit', 'smoothie': 'smoothie',
    'no-extrusion': 'no-extrusion',
}

SUPPORT_STYLE_MAP = {
    'grid':       ('grid',        False),
    'snug':       ('snug',        False),
    'organic':    ('tree_strong', True),   # approx
    'tree':       ('tree_auto',   True),   # approx
    'with_sheath':('default',     True),   # approx
}

IRONING_TYPE_MAP = {
    'top': 'top', 'topmost': 'topmost', 'solid': 'solid',
}

PERIMETER_GENERATOR_MAP = {
    'arachne': 'arachne', 'classic': 'classic',
}

FUZZY_SKIN_MAP = {
    'none': 'none', 'external': 'outer wall',
    'all': 'all walls', 'allwalls': 'all walls',
}


def _map(val, mapping, approx_default=False):
    """Retourne (orca_val, is_approx)."""
    result = mapping.get(val)
    if result is None:
        return val, approx_default
    if isinstance(result, tuple):
        return result
    return result, False


# =================== INI PARSER ===================

def parse_ini(ini_path):
    sections = {}
    current_section = None
    current_data = {}

    with open(ini_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and ']' in line:
                if current_section:
                    sections[current_section] = current_data
                current_section = line[1:line.index(']')]
                current_data = {}
            elif '=' in line and current_section:
                key, _, value = line.partition('=')
                current_data[key.strip()] = value.strip()

    if current_section:
        sections[current_section] = current_data
    return sections


# =================== HELPERS ===================

def split_csv(val):
    return [v.strip() for v in val.split(',')]

def bed_shape_to_area(val):
    return split_csv(val)

def clean_gcode(val):
    val = val.strip('"')
    val = val.replace('\\n', '\n')
    return val

def set_if_v(out, key, val):
    if val is not None:
        out[key] = val


# =================== PRINT PROFILE ===================

def convert_print_profile(name, data, sl=None):
    out = {
        'name': name, 'from': 'User', 'inherits': '',
        'print_settings_id': name, 'version': '1.9.0.0',
    }

    def g(key, default=None):
        v = data.get(key, default)
        return default if v in (None, 'nil') else v

    def si(orca_key, prusa_key, transform=None, note='', approx=False):
        v = g(prusa_key)
        if v is not None:
            val = transform(v) if transform else v
            out[orca_key] = val
            if sl: sl.log(prusa_key, orca_key, val, note, approx)

    def si_nonzero(orca_key, prusa_key, note='', approx=False):
        v = g(prusa_key)
        if v and v != '0':
            out[orca_key] = v
            if sl: sl.log(prusa_key, orca_key, v, note, approx)

    # Layer
    si('layer_height',             'layer_height')
    si('initial_layer_print_height','first_layer_height')

    # Walls
    si('wall_loops',    'perimeters')
    si('wall_generator','perimeter_generator',
       lambda v: _map(v, PERIMETER_GENERATOR_MAP)[0])
    si('outer_wall_speed',     'external_perimeter_speed')
    si('inner_wall_speed',     'perimeter_speed')
    si('small_perimeter_speed','small_perimeter_speed')
    si_nonzero('outer_wall_line_width', 'external_perimeter_extrusion_width')
    si_nonzero('inner_wall_line_width', 'perimeter_extrusion_width')
    si('ensure_vertical_shell_thickness', 'ensure_vertical_shell_thickness',
       lambda v: 'ensure_all_walls' if v == 'enabled' else ('none' if v == 'disabled' else v))
    si('extra_perimeters_on_overhangs', 'extra_perimeters_on_overhangs')
    si('detect_overhang_wall', 'overhangs')
    si('detect_thin_wall',     'thin_walls')

    # Shells
    si('top_shell_layers',    'top_solid_layers')
    si('bottom_shell_layers', 'bottom_solid_layers')
    si_nonzero('top_shell_thickness',    'top_solid_min_thickness')
    si_nonzero('bottom_shell_thickness', 'bottom_solid_min_thickness')

    # Top/Bottom
    si('top_surface_pattern',    'top_fill_pattern',
       lambda v: _map(v, SURFACE_PATTERN_MAP)[0])
    si('bottom_surface_pattern', 'bottom_fill_pattern',
       lambda v: _map(v, SURFACE_PATTERN_MAP)[0])
    si('top_surface_speed',    'top_solid_infill_speed')
    si_nonzero('top_surface_line_width', 'top_infill_extrusion_width')

    # Infill
    si('sparse_infill_density',  'fill_density')
    si('sparse_infill_pattern',  'fill_pattern',
       lambda v: _map(v, FILL_PATTERN_MAP)[0])
    si('infill_direction',       'fill_angle')
    si('sparse_infill_speed',    'infill_speed')
    si('internal_solid_infill_speed', 'solid_infill_speed')
    si('infill_wall_overlap',    'infill_overlap')
    si('infill_anchor',          'infill_anchor')
    si('infill_anchor_max',      'infill_anchor_max')
    si_nonzero('sparse_infill_line_width',         'infill_extrusion_width')
    si_nonzero('internal_solid_infill_line_width', 'solid_infill_extrusion_width')

    # First layer
    si('initial_layer_speed', 'first_layer_speed')
    v = g('first_layer_infill_speed')
    if v and v != '0':
        out['initial_layer_infill_speed'] = v
        if sl: sl.log('first_layer_infill_speed', 'initial_layer_infill_speed', v)
    si_nonzero('initial_layer_line_width', 'first_layer_extrusion_width')

    # Travel
    si('travel_speed', 'travel_speed')
    si_nonzero('travel_speed_z', 'travel_speed_z')

    # Gap fill
    gap_enabled = g('gap_fill_enabled', '1')
    if sl and gap_enabled is not None: sl._consumed.add('gap_fill_enabled')
    v = g('gap_fill_speed')
    if v:
        val = v if gap_enabled != '0' else '0'
        out['gap_infill_speed'] = val
        if sl: sl.log('gap_fill_speed', 'gap_infill_speed', val,
                      '' if gap_enabled != '0' else 'désactivé → 0')

    # Bridge
    si('bridge_speed', 'bridge_speed')
    si('bridge_flow',  'bridge_flow_ratio')
    si('bridge_angle', 'bridge_angle')
    v = g('over_bridge_speed')
    if v and v != '0':
        out['internal_bridge_speed'] = v
        if sl: sl.log('over_bridge_speed', 'internal_bridge_speed', v, '', True)

    # Seam
    v = g('seam_position')
    if v is not None:
        orca_v, approx = _map(v, SEAM_POSITION_MAP)
        out['seam_position'] = orca_v
        if sl: sl.log('seam_position', 'seam_position', orca_v,
                      'contiguous→nearest (approx)' if approx else '', approx)

    # Ironing
    ironing = g('ironing')
    ironing_type_raw = g('ironing_type', 'top')
    if sl and ironing_type_raw is not None: sl._consumed.add('ironing_type')
    if ironing == '1':
        orca_ir = _map(ironing_type_raw, IRONING_TYPE_MAP)[0]
        out['ironing_type'] = orca_ir
        if sl: sl.log('ironing', 'ironing_type', orca_ir)
    elif ironing == '0':
        out['ironing_type'] = 'no ironing'
        if sl: sl.log('ironing', 'ironing_type', 'no ironing')
    si('ironing_speed',   'ironing_speed')
    si('ironing_flow',    'ironing_flowrate')
    si('ironing_spacing', 'ironing_spacing')

    # Skirt/Brim
    si('skirt_loops',    'skirts')
    si('skirt_distance', 'skirt_distance')
    si('brim_width',     'brim_width')
    v = g('brim_type')
    if v:
        orca_v = _map(v, BRIM_TYPE_MAP)[0]
        out['brim_type'] = orca_v
        if sl: sl.log('brim_type', 'brim_type', orca_v)
    si('brim_object_gap', 'brim_separation')

    # Raft
    si('raft_layers', 'raft_layers')

    # Support
    si('enable_support',            'support_material')
    si('support_auto',              'support_material_auto')
    si('support_threshold_angle',   'support_material_threshold')
    si('support_on_build_plate_only','support_material_buildplate_only')
    v = g('support_material_style')
    if v:
        orca_v, approx = _map(v, SUPPORT_STYLE_MAP)
        out['support_style'] = orca_v
        if sl: sl.log('support_material_style', 'support_style', orca_v,
                      'organic→tree_strong (approx)' if approx else '', approx)
    si('support_base_pattern_spacing','support_material_spacing')
    si('support_speed',              'support_material_speed')
    si('support_top_z_distance',     'support_material_contact_distance')
    si('support_interface_spacing',  'support_material_interface_spacing')
    si('support_interface_speed',    'support_material_interface_speed')
    v = g('support_material_bottom_contact_distance')
    if v and v != '0':
        out['support_bottom_z_distance'] = v
        if sl: sl.log('support_material_bottom_contact_distance', 'support_bottom_z_distance', v)
    v = g('support_material_interface_layers')
    if v and v != '-1':
        out['support_interface_top_layers'] = v
        if sl: sl.log('support_material_interface_layers', 'support_interface_top_layers', v)

    # Tree support
    si('tree_support_branch_angle',    'support_tree_angle')
    si('tree_support_tip_diameter',    'support_tree_tip_diameter')
    si('tree_support_branch_diameter', 'support_tree_branch_diameter')

    # Misc
    si('spiral_mode',          'spiral_vase')
    si_nonzero('resolution',   'resolution')
    si('gcode_resolution',     'gcode_resolution')
    si('enable_prime_tower',   'wipe_tower')
    si('prime_tower_width',    'wipe_tower_width')
    v = g('only_retract_when_crossing_perimeters')
    if v:
        out['reduce_crossing_wall'] = v
        if sl: sl.log('only_retract_when_crossing_perimeters', 'reduce_crossing_wall', v)
    si_nonzero('max_volumetric_speed', 'max_volumetric_speed')
    v = g('complete_objects')
    if v:
        val = 'by object' if v == '1' else 'by layer'
        out['print_sequence'] = val
        if sl: sl.log('complete_objects', 'print_sequence', val)
    si('filename_format',        'output_filename_format')
    si('xy_contour_compensation','xy_size_compensation')
    v = g('fuzzy_skin')
    if v:
        orca_v = _map(v, FUZZY_SKIN_MAP)[0]
        out['fuzzy_skin'] = orca_v
        if sl: sl.log('fuzzy_skin', 'fuzzy_skin', orca_v)
    si('fuzzy_skin_thickness',      'fuzzy_skin_thickness')
    si('fuzzy_skin_point_distance', 'fuzzy_skin_point_dist')

    # Accelerations
    for pk, ok in [
        ('perimeter_acceleration',          'inner_wall_acceleration'),
        ('external_perimeter_acceleration', 'outer_wall_acceleration'),
        ('infill_acceleration',             'sparse_infill_acceleration'),
        ('solid_infill_acceleration',       'internal_solid_infill_acceleration'),
        ('top_solid_infill_acceleration',   'top_surface_acceleration'),
        ('travel_acceleration',             'travel_acceleration'),
        ('bridge_acceleration',             'bridge_acceleration'),
        ('first_layer_acceleration',        'initial_layer_acceleration'),
        ('default_acceleration',            'default_acceleration'),
    ]:
        v = g(pk)
        if v and v != '0':
            out[ok] = v
            if sl: sl.log(pk, ok, v)

    # Overhang speeds (indexation inversée)
    for pk, ok in [
        ('overhang_speed_0', 'overhang_4_4_speed'),
        ('overhang_speed_1', 'overhang_3_4_speed'),
        ('overhang_speed_2', 'overhang_2_4_speed'),
        ('overhang_speed_3', 'overhang_1_4_speed'),
    ]:
        v = g(pk)
        if v:
            out[ok] = v
            if sl: sl.log(pk, ok, v, 'index inversé Prusa→Orca', True)

    v = g('notes')
    if v:
        out['notes'] = v
        if sl: sl.log('notes', 'notes', v)
    v = g('gcode_label_objects')
    if v:
        val = '0' if v == 'disabled' else '1'
        out['label_objects'] = val
        if sl: sl.log('gcode_label_objects', 'label_objects', val)

    # Elephant foot
    si('elefant_foot_compensation', 'elephant_foot_compensation')

    # Outer wall first
    si('outer_wall_first', 'external_perimeters_first')

    # Crossing perimeters detour
    si('max_travel_detour_distance', 'avoid_crossing_perimeters_max_detour')

    # Arc fitting (PrusaSlicer uses 'disabled'/'enabled', Orca uses 0/1)
    v = g('arc_fitting')
    if v is not None:
        val = '0' if v == 'disabled' else '1'
        out['enable_arc_fitting'] = val
        if sl: sl.log('arc_fitting', 'enable_arc_fitting', val)

    # Draft shield
    si('draft_shield', 'draft_shield')

    # Interface shells
    si('interface_shells', 'interface_shells')

    # Staggered seams
    si('staggered_inner_seams', 'staggered_inner_seams')

    # Gcode comments
    si('gcode_comments', 'gcode_comments')

    # Don't support bridges
    si('bridge_no_support', 'dont_support_bridges')

    # Slowdown for curled perimeters
    si('slowdown_for_curled_perimeters', 'slowdown_for_curled_perimeters')

    # Skirt extras
    si('skirt_height', 'skirt_height')
    si_nonzero('min_skirt_length', 'min_skirt_length')

    # Support extras
    si('support_base_pattern',      'support_material_pattern')
    si('support_object_xy_distance','support_material_xy_spacing')
    si_nonzero('support_line_width','support_material_extrusion_width')
    v = g('support_material_bottom_interface_layers')
    if v is not None:
        if sl: sl._consumed.add('support_material_bottom_interface_layers')
        if v != '-1':
            out['support_interface_bottom_layers'] = v
            if sl: sl.log('support_material_bottom_interface_layers','support_interface_bottom_layers', v)
    v = g('support_material_interface_contact_loops')
    if v:
        # PrusaSlicer bool → Orca enum (default / rectilinear_interlaced)
        orca_v = 'default' if v == '0' else 'rectilinear_interlaced'
        out['support_interface_loop_pattern'] = orca_v
        if sl: sl.log('support_material_interface_contact_loops','support_interface_loop_pattern', orca_v, '', True)
    si('tree_support_wall_count', 'tree_support_wall_count')

    # Raft extras
    si('raft_contact_distance',       'raft_contact_distance')
    si('raft_expansion',              'raft_expansion')
    si('raft_first_layer_density',    'raft_first_layer_density')
    si('raft_first_layer_expansion',  'raft_first_layer_expansion')

    # Wipe tower extras
    si('wipe_tower_x',              'wipe_tower_x')
    si('wipe_tower_y',              'wipe_tower_y')
    si('wipe_tower_rotation_angle', 'wipe_tower_rotation_angle')
    si('prime_tower_brim_width',    'wipe_tower_brim_width')
    si('wipe_tower_bridging',       'wipe_tower_bridging')
    v = g('wipe_tower_no_sparse_layers')
    if v:
        out['wipe_tower_no_sparse_layers'] = v
        if sl: sl.log('wipe_tower_no_sparse_layers','wipe_tower_no_sparse_layers', v)

    # Hole compensation
    si('xy_hole_compensation', 'xy_inner_size_compensation')

    # Default line width
    si_nonzero('line_width', 'extrusion_width')

    # Arachne parameters
    si('min_bead_width',   'min_bead_width')
    si('min_feature_size', 'min_feature_size')
    si('wall_distribution_count',       'wall_distribution_count')
    si('wall_transition_angle',         'wall_transition_angle')
    si('wall_transition_filter_deviation','wall_transition_filter_deviation')
    si('wall_transition_length',        'wall_transition_length')

    # Bridges
    si('thick_bridges', 'thick_bridges')

    # Seam gap
    v = g('seam_gap_distance')
    if v:
        out['seam_gap'] = v
        if sl: sl.log('seam_gap_distance', 'seam_gap', v)

    # Slicing mode
    si('slicing_mode', 'slicing_mode')

    # Standby temp (ooze prevention)
    si('standby_temperature_delta', 'standby_temperature_delta')

    if sl: sl.finalize(data)
    return out


# =================== FILAMENT PROFILE ===================

def convert_filament_profile(name, data, sl=None):
    out = {
        'name': name, 'from': 'User', 'inherits': '',
        'filament_settings_id': [name], 'version': '1.9.0.0',
    }

    def g(key, default=None):
        v = data.get(key, default)
        return default if v in (None, 'nil') else v

    def arr(v): return [v]

    def sa(ok, pk, note='', approx=False):
        v = g(pk)
        if v is not None:
            out[ok] = arr(v)
            if sl: sl.log(pk, ok, v, note, approx)

    # Temperatures
    sa('nozzle_temperature',              'temperature')
    sa('nozzle_temperature_initial_layer','first_layer_temperature')
    sa('hot_plate_temp',                  'bed_temperature')
    sa('hot_plate_temp_initial_layer',    'first_layer_bed_temperature')
    v = g('chamber_temperature')
    if v and v != '0':
        out['chamber_temperature'] = arr(v)
        if sl: sl.log('chamber_temperature', 'chamber_temperature', v)

    # Fan
    sa('fan_min_speed',               'min_fan_speed')
    sa('fan_max_speed',               'max_fan_speed')
    sa('overhang_fan_speed',          'bridge_fan_speed', 'bridge→overhang (approx)', True)
    sa('close_fan_the_first_x_layers','disable_fan_first_layers')
    sa('fan_cooling_layer_time',      'fan_below_layer_time')
    sa('full_fan_speed_layer',        'full_fan_speed_layer')

    # Cooling
    sa('slow_down_layer_time','slowdown_below_layer_time')
    sa('slow_down_min_speed', 'min_print_speed')

    # Extrusion
    sa('filament_flow_ratio','extrusion_multiplier')
    v = g('filament_max_volumetric_speed')
    if v and v != '0':
        out['filament_max_volumetric_speed'] = arr(v)
        if sl: sl.log('filament_max_volumetric_speed','filament_max_volumetric_speed', v)

    # Filament properties
    sa('filament_type',           'filament_type')
    sa('default_filament_colour', 'filament_colour')
    v = g('filament_density')
    if v and v != '0':
        out['filament_density'] = arr(v)
        if sl: sl.log('filament_density','filament_density', v)
    v = g('filament_cost')
    if v and v != '0':
        out['filament_cost'] = arr(v)
        if sl: sl.log('filament_cost','filament_cost', v)
    v = g('filament_notes', '').strip('"')
    if v:
        out['filament_notes'] = v
        if sl: sl.log('filament_notes','filament_notes', v)

    # Retraction overrides
    for pk, ok in [
        ('filament_retract_length',       'filament_retraction_length'),
        ('filament_retract_speed',        'filament_retraction_speed'),
        ('filament_deretract_speed',      'filament_deretraction_speed'),
        ('filament_retract_layer_change', 'filament_retract_when_changing_layer'),
        ('filament_retract_lift',         'filament_z_hop'),
        ('filament_retract_before_travel','filament_retraction_minimum_travel'),
        ('filament_retract_before_wipe',  'filament_retract_before_wipe'),
        ('filament_wipe',                 'filament_wipe'),
    ]:
        v = g(pk)
        if v is not None:
            out[ok] = arr(v)
            if sl: sl.log(pk, ok, v)

    # Vendor
    raw_vendor = g('filament_vendor', '')
    if sl and raw_vendor: sl._consumed.add('filament_vendor')
    v = raw_vendor.strip('"()')
    if v and v.lower() not in ('unknown', ''):
        out['filament_vendor'] = v
        if sl: sl.log('filament_vendor', 'filament_vendor', v)

    # Minimal purge for wipe tower
    v = g('filament_minimal_purge_on_wipe_tower')
    if v and v != '0':
        out['filament_minimal_purge_on_wipe_tower'] = arr(v)
        if sl: sl.log('filament_minimal_purge_on_wipe_tower','filament_minimal_purge_on_wipe_tower', v)

    # Multitool ramming flow
    v = g('filament_multitool_ramming_flow')
    if v and v != '0':
        out['filament_multitool_ramming_flow'] = arr(v)
        if sl: sl.log('filament_multitool_ramming_flow','filament_multitool_ramming_flow', v)

    # Overhang fan speed (use zone 0 = highest overhang as Orca's single value)
    v = g('overhang_fan_speed_0')
    if v and v != '0':
        out['overhang_fan_speed'] = arr(v)
        if sl: sl.log('overhang_fan_speed_0', 'overhang_fan_speed', v, 'zone 0 (max overhang)', False)
        # Set threshold to 50% (moderate overhang)
        out['overhang_fan_threshold'] = arr('50%')
        if sl: sl.log('overhang_fan_speed_0', 'overhang_fan_threshold', '50%', 'seuil fixé à 50% (approx)', True)

    # Filament physical properties
    v = g('filament_diameter')
    if v and v != '0':
        out['filament_diameter'] = arr(v)
        if sl: sl.log('filament_diameter','filament_diameter', v)
    v = g('filament_soluble')
    if v:
        out['filament_soluble'] = arr(v)
        if sl: sl.log('filament_soluble','filament_soluble', v)
    v = g('filament_shrink')
    if v and v != '100%' and v != '100':
        out['filament_shrink'] = arr(v)
        if sl: sl.log('filament_shrink','filament_shrink', v)

    # MMU / toolchanger filament motion
    for pk, ok in [
        ('filament_loading_speed',          'filament_loading_speed'),
        ('filament_loading_speed_start',    'filament_loading_speed_start'),
        ('filament_load_time',              'filament_load_time'),
        ('filament_unloading_speed',        'filament_unloading_speed'),
        ('filament_unloading_speed_start',  'filament_unloading_speed_start'),
        ('filament_unload_time',            'filament_unload_time'),
        ('filament_toolchange_delay',       'filament_toolchange_delay'),
        ('filament_cooling_moves',          'filament_cooling_moves'),
        ('filament_cooling_initial_speed',  'filament_cooling_initial_speed'),
        ('filament_cooling_final_speed',    'filament_cooling_final_speed'),
        ('filament_stamping_loading_speed', 'filament_stamping_loading_speed'),
    ]:
        v = g(pk)
        if v is not None:
            out[ok] = arr(v)
            if sl: sl.log(pk, ok, v)

    # GCode
    v = g('start_filament_gcode', '')
    out['filament_start_gcode'] = clean_gcode(v)
    if sl and v.strip('"'): sl.log('start_filament_gcode','filament_start_gcode','<gcode>')

    v = g('end_filament_gcode', '')
    out['filament_end_gcode'] = clean_gcode(v)
    if sl and v.strip('"'): sl.log('end_filament_gcode','filament_end_gcode','<gcode>')

    if sl: sl.finalize(data)
    return out


# =================== PRINTER PROFILE ===================

def convert_printer_profile(name, data, sl=None):
    out = {
        'name': name, 'from': 'User', 'inherits': '',
        'printer_settings_id': name, 'printer_technology': 'FFF',
        'version': '1.9.0.0',
    }

    def g(key, default=None):
        v = data.get(key, default)
        return default if v is None else v

    def si(ok, pk, note='', approx=False):
        v = g(pk)
        if v:
            out[ok] = v
            if sl: sl.log(pk, ok, v, note, approx)

    # Bed
    v = g('bed_shape')
    if v:
        out['printable_area'] = bed_shape_to_area(v)
        if sl: sl.log('bed_shape','printable_area', v)
    si('printable_height', 'max_print_height')
    v = g('min_layer_height')
    if v:
        out['min_layer_height'] = [v]
        if sl: sl.log('min_layer_height','min_layer_height', v)
    v = g('max_layer_height')
    if v and v != '0':
        out['max_layer_height'] = [v]
        if sl: sl.log('max_layer_height','max_layer_height', v)

    # Nozzle
    v = g('nozzle_diameter', '0.4')
    out['nozzle_diameter'] = [v]
    out['printer_variant'] = v
    if sl: sl.log('nozzle_diameter','nozzle_diameter', v)

    # GCode flavor
    v = g('gcode_flavor')
    if v:
        orca_v = _map(v, GCODE_FLAVOR_MAP)[0]
        out['gcode_flavor'] = orca_v
        if sl: sl.log('gcode_flavor','gcode_flavor', orca_v)

    # GCode scripts
    for pk, ok in [
        ('start_gcode',       'machine_start_gcode'),
        ('end_gcode',         'machine_end_gcode'),
        ('before_layer_gcode','before_layer_change_gcode'),
        ('layer_gcode',       'layer_change_gcode'),
    ]:
        v = g(pk, '')
        out[ok] = clean_gcode(v)
        if sl and v: sl.log(pk, ok, '<gcode>')

    for pk, ok in [
        ('pause_print_gcode',    'machine_pause_gcode'),
        ('color_change_gcode',   'change_filament_gcode'),
        ('toolchange_gcode',     'toolchange_gcode'),
        ('template_custom_gcode','template_custom_gcode'),
    ]:
        v = g(pk)
        if v:
            out[ok] = v
            if sl: sl.log(pk, ok, v)

    # Extruder clearance
    v = g('extruder_clearance_height')
    if v:
        out['extruder_clearance_height_to_lid'] = v
        if sl: sl.log('extruder_clearance_height','extruder_clearance_height_to_lid', v, '', True)
    si('extruder_clearance_radius',         'extruder_clearance_radius')
    si('extruder_clearance_height_to_rod',  'extruder_clearance_height_to_rod')

    # Retraction
    for pk, ok in [
        ('retract_length',         'retraction_length'),
        ('retract_speed',          'retraction_speed'),
        ('retract_lift',           'z_hop'),
        ('retract_lift_above',     'retract_lift_above'),
        ('retract_lift_below',     'retract_lift_below'),
        ('retract_before_travel',  'retraction_minimum_travel'),
        ('retract_before_wipe',    'retract_before_wipe'),
        ('retract_layer_change',   'retract_when_changing_layer'),
        ('retract_restart_extra',  'retract_restart_extra'),
        ('wipe',                   'wipe'),
    ]:
        v = g(pk)
        if v is not None:
            out[ok] = [v]
            if sl: sl.log(pk, ok, v)
    v = g('deretract_speed')
    if v and v != '0':
        out['deretraction_speed'] = [v]
        if sl: sl.log('deretract_speed','deretraction_speed', v)
    for pk, ok in [
        ('retract_length_toolchange',        'retract_length_toolchange'),
        ('retract_restart_extra_toolchange', 'retract_restart_extra_toolchange'),
    ]:
        v = g(pk)
        if v is not None:
            out[ok] = [v]
            if sl: sl.log(pk, ok, v)

    # Machine limits
    for pk, ok in [
        ('machine_max_acceleration_x',          'machine_max_acceleration_x'),
        ('machine_max_acceleration_y',          'machine_max_acceleration_y'),
        ('machine_max_acceleration_z',          'machine_max_acceleration_z'),
        ('machine_max_acceleration_e',          'machine_max_acceleration_e'),
        ('machine_max_acceleration_extruding',  'machine_max_acceleration_extruding'),
        ('machine_max_acceleration_retracting', 'machine_max_acceleration_retracting'),
        ('machine_max_acceleration_travel',     'machine_max_acceleration_travel'),
        ('machine_max_feedrate_x',              'machine_max_speed_x'),
        ('machine_max_feedrate_y',              'machine_max_speed_y'),
        ('machine_max_feedrate_z',              'machine_max_speed_z'),
        ('machine_max_feedrate_e',              'machine_max_speed_e'),
        ('machine_max_jerk_x',                  'machine_max_jerk_x'),
        ('machine_max_jerk_y',                  'machine_max_jerk_y'),
        ('machine_max_jerk_z',                  'machine_max_jerk_z'),
        ('machine_max_jerk_e',                  'machine_max_jerk_e'),
        ('machine_min_extruding_rate',          'machine_min_extruding_rate'),
        ('machine_min_travel_rate',             'machine_min_travel_rate'),
        ('machine_max_junction_deviation',      'machine_max_junction_deviation'),
    ]:
        v = g(pk)
        if v:
            out[ok] = split_csv(v)
            if sl: sl.log(pk, ok, v)

    # Misc
    for pk, ok in [
        ('use_relative_e_distances',    'use_relative_e_distances'),
        ('use_firmware_retraction',     'use_firmware_retraction'),
        ('silent_mode',                 'silent_mode'),
        ('z_offset',                    'z_offset'),
        ('printer_notes',               'printer_notes'),
        ('thumbnails',                  'thumbnails'),
        ('thumbnails_format',           'thumbnails_format'),
        ('cooling_tube_length',         'cooling_tube_length'),
        ('cooling_tube_retraction',     'cooling_tube_retraction'),
        ('parking_pos_retraction',      'parking_pos_retraction'),
        ('extra_loading_move',          'extra_loading_move'),
        ('high_current_on_filament_swap','high_current_on_filament_swap'),
    ]:
        v = g(pk)
        if v:
            out[ok] = v
            if sl: sl.log(pk, ok, v)

    out['extruder_offset']     = ['0x0']
    out['extruder_colour']     = [g('extruder_colour', '').strip('"') or '#FFFFFF']
    out['extruder_type']       = ['Direct Drive']
    out['printer_extruder_id'] = ['1']

    if sl: sl.finalize(data)
    return out


# =================== BUNDLE STRUCTURE ===================

def create_bundle_structure(printer_name, filament_files, process_files, printer_files):
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    bundle_id = f'{abs(hash(printer_name)) % 10000000000}_{printer_name}_{ts}'
    return {
        'bundle_id':          bundle_id,
        'bundle_type':        'printer config bundle',
        'filament_config':    filament_files,
        'printer_config':     printer_files,
        'printer_preset_name': printer_name,
        'process_config':     process_files,
        'version':            '02.03.00.62',
    }


# =================== MAIN CONVERTER ===================

def convert_ini_to_orca(ini_path, output_path=None, log=None):
    ini_path = Path(ini_path)
    if not ini_path.exists():
        raise FileNotFoundError(f'Fichier introuvable : {ini_path}')

    sections = parse_ini(ini_path)

    print_sections    = {k[len('print:'):]:    v for k, v in sections.items() if k.startswith('print:')}
    filament_sections = {k[len('filament:'):]: v for k, v in sections.items() if k.startswith('filament:')}
    printer_sections  = {k[len('printer:'):]:  v for k, v in sections.items() if k.startswith('printer:')}

    if not printer_sections:
        if log: log.warn('Aucune section [printer:...] trouvée')
        printer_name = ini_path.stem
    else:
        printer_name = list(printer_sections.keys())[0]

    if output_path is None:
        output_path = ini_path.parent / f'{printer_name}.orca_printer'
    output_path = Path(output_path)

    printer_files = []
    filament_files = []
    process_files = []
    converted = {}

    for name, data in printer_sections.items():
        fname = f'printer/{name}.json'
        printer_files.append(fname)
        sl = log.new_section(name, 'printer') if log else None
        converted[fname] = convert_printer_profile(name, data, sl)

    for name, data in filament_sections.items():
        fname = f'filament/{name}.json'
        filament_files.append(fname)
        sl = log.new_section(name, 'filament') if log else None
        converted[fname] = convert_filament_profile(name, data, sl)

    for name, data in print_sections.items():
        fname = f'process/{name}.json'
        process_files.append(fname)
        sl = log.new_section(name, 'process') if log else None
        converted[fname] = convert_print_profile(name, data, sl)

    bundle = create_bundle_structure(printer_name, filament_files, process_files, printer_files)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('bundle_structure.json',
                    json.dumps(bundle, indent=2, ensure_ascii=False))
        for fname, data in converted.items():
            zf.writestr(fname, json.dumps(data, indent=2, ensure_ascii=False))

    return output_path


# =================== CLI ===================

def main():
    parser = argparse.ArgumentParser(
        description='Convert PrusaSlicer config bundle (.ini) to OrcaSlicer (.orca_printer)'
    )
    parser.add_argument('input')
    parser.add_argument('-o', '--output', default=None)
    args = parser.parse_args()
    result = convert_ini_to_orca(args.input, args.output)
    print(f'✅  {result}')

if __name__ == '__main__':
    main()
