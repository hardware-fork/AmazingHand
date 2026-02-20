// Copyright (C) Julia Jia
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#![allow(dead_code)] // Facet-derived struct fields are used by (de)serialization, not always in this crate

use facet::Facet;
use std::fs;
use std::path::{Path, PathBuf};

const DEG_TO_RAD: f64 = std::f64::consts::PI / 180.0;

/// Fallback finger order when geometry file is missing or not used.
const DEFAULT_FINGER_ORDER: &[&str] = &["index", "middle", "ring", "thumb"];

fn default_finger_order() -> Vec<String> {
    DEFAULT_FINGER_ORDER.iter().map(ToString::to_string).collect()
}

#[derive(Debug, Clone, Facet)]
pub struct Fingers {
    pub motors: Vec<Motors>,
}

#[derive(Debug, Clone, Facet)]
pub struct Motors {
    pub finger_name: String,
    pub motor1: Motor,
    pub motor2: Motor,
}

#[derive(Debug, Clone, Facet)]
pub struct Motor {
    pub id: u8,
    pub offset: f64,
    pub invert: bool,
    pub model: String,
}

/// Load finger order from hand_geometry.toml (key "fingers" = array of strings).
fn load_finger_order_from_path(geometry_path: &Path) -> Result<Vec<String>, String> {
    let s = fs::read_to_string(geometry_path).map_err(|e| e.to_string())?;
    load_finger_order_from_str(&s)
}

fn load_finger_order_from_str(geometry_toml: &str) -> Result<Vec<String>, String> {
    let value: toml::Value = toml::from_str(geometry_toml).map_err(|e| e.to_string())?;
    let root = value.as_table().ok_or("hand_geometry: expected top-level table")?;
    let arr = root
        .get("fingers")
        .and_then(|v| v.as_array())
        .ok_or("hand_geometry: missing key 'fingers'")?;
    let order: Vec<String> = arr
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect();
    if order.is_empty() {
        return Err("hand_geometry: 'fingers' must be non-empty".into());
    }
    Ok(order)
}

/// Maps anatomical name (index, middle, ring, thumb) to legacy finger_name (r_finger1..4 or l_finger1..4).
/// Legacy names are used by: main.rs (metadata.parameters key), get_zeros.rs, set_zeros.rs,
/// AHSimulation/mj_mink_right.py, mj_mink_left.py (metadata keys), and legacy TOML configs (r_hand.toml, 2hands.toml).
/// TODO: refactor consumers to use anatomical names and remove this mapping.
fn anatomical_to_legacy_name(anatomical: &str, right_hand: bool) -> String {
    let prefix = if right_hand { "r_finger" } else { "l_finger" };
    match anatomical {
        "index" => format!("{}1", prefix),
        "middle" => format!("{}2", prefix),
        "ring" => format!("{}3", prefix),
        "thumb" => format!("{}4", prefix),
        _ => format!("{}_{}", prefix, anatomical),
    }
}

fn parse_finger_section(
    root: &toml::map::Map<String, toml::Value>,
    name: &str,
    right_hand: bool,
) -> Result<Motors, String> {
    let section = root
        .get(name)
        .and_then(|v| v.as_table())
        .ok_or_else(|| format!("canonical calibration missing section [{}]", name))?;
    let ids: Vec<i64> = section
        .get("ids")
        .and_then(|v| v.as_array())
        .ok_or_else(|| format!("[{}] missing ids", name))?
        .iter()
        .filter_map(|v| v.as_integer())
        .collect();
    let rest_deg: Vec<f64> = section
        .get("rest_deg")
        .and_then(|v| v.as_array())
        .ok_or_else(|| format!("[{}] missing rest_deg", name))?
        .iter()
        .map(|v| v.as_float().unwrap_or_else(|| v.as_integer().unwrap_or(0) as f64))
        .collect();
    if ids.len() < 2 || rest_deg.len() < 2 {
        return Err(format!("[{}] needs ids and rest_deg with at least 2 elements", name));
    }
    let motor = |id: i64, rest: f64| Motor {
        id: id as u8,
        offset: rest * DEG_TO_RAD,
        invert: false,
        model: "SCS0009".to_string(),
    };
    Ok(Motors {
        finger_name: anatomical_to_legacy_name(name, right_hand),
        motor1: motor(ids[0], rest_deg[0]),
        motor2: motor(ids[1], rest_deg[1]),
    })
}

/// Build Fingers from canonical calibration TOML (tables per finger with ids and rest_deg).
/// right_hand: true for r_finger1..4, false for l_finger1..4.
fn parse_canonical_calibration(
    toml_str: &str,
    finger_order: &[String],
    right_hand: bool,
) -> Result<Fingers, String> {
    let value: toml::Value = toml::from_str(toml_str).map_err(|e| e.to_string())?;
    let root = value.as_table().ok_or("expected top-level table")?;
    let motors: Vec<Motors> = finger_order
        .iter()
        .map(|name| parse_finger_section(root, name, right_hand))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Fingers { motors })
}

/// Detect if the TOML is canonical format (has [index] with ids).
fn is_canonical_format(toml_str: &str) -> bool {
    let value: toml::Value = match toml::from_str(toml_str) {
        Ok(v) => v,
        Err(_) => return false,
    };
    let root = match value.as_table() {
        Some(t) => t,
        None => return false,
    };
    root.get("index")
        .and_then(|v| v.as_table())
        .and_then(|t| t.get("ids"))
        .is_some()
}

/// Resolve hand_geometry.toml path from a calibration file path.
/// E.g. config/calibration/r_hand.toml -> config/hand_geometry.toml; config/r_hand.toml -> config/hand_geometry.toml.
pub fn geometry_path_for_calibration(cal_path: &Path) -> PathBuf {
    let parent = cal_path.parent().unwrap_or_else(|| Path::new("."));
    let config_dir = if parent.file_name().map(|n| n == "calibration").unwrap_or(false) {
        parent.parent().unwrap_or(parent)
    } else {
        parent
    };
    config_dir.join("hand_geometry.toml")
}

/// Infer right hand from calibration path (e.g. l_hand_*.toml -> false, r_hand_*.toml or other -> true).
fn right_hand_from_path(path: &Path) -> bool {
    path.file_name()
        .and_then(|n| n.to_str())
        .map(|s| !s.starts_with("l_hand"))
        .unwrap_or(true)
}

fn finger_order_from_geometry_path(geometry_path: &Path) -> Vec<String> {
    load_finger_order_from_path(geometry_path).unwrap_or_else(|_| default_finger_order())
}

/// Load Fingers from a config file. Supports legacy (facet) and canonical calibration TOML.
/// For canonical format, finger order is read from hand_geometry.toml next to the config dir (derived from calibration path).
pub fn load_fingers_from_path(path: &Path) -> Result<Fingers, String> {
    let toml_str = fs::read_to_string(path).map_err(|e| e.to_string())?;
    if is_canonical_format(&toml_str) {
        let geometry_path = geometry_path_for_calibration(path);
        let order = finger_order_from_geometry_path(&geometry_path);
        let right_hand = right_hand_from_path(path);
        parse_canonical_calibration(&toml_str, &order, right_hand)
    } else {
        load_fingers_from_str(&toml_str, None)
    }
}

/// Load Fingers from TOML string. Supports legacy (facet) and canonical calibration format.
/// For canonical format, pass geometry_path to load finger order from hand_geometry.toml; if None, uses DEFAULT_FINGER_ORDER.
/// When loading from string, hand side is unknown so right_hand is assumed (r_finger1..4).
pub fn load_fingers_from_str(toml_str: &str, geometry_path: Option<&Path>) -> Result<Fingers, String> {
    if is_canonical_format(toml_str) {
        let order = geometry_path
            .map(finger_order_from_geometry_path)
            .unwrap_or_else(default_finger_order);
        parse_canonical_calibration(toml_str, &order, true)
    } else {
        facet_toml::from_str(toml_str).map_err(|e| e.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const CANONICAL_SAMPLE: &str = r#"
[index]
ids = [1, 2]
rest_deg = [-2, 0]

[middle]
ids = [3, 4]
rest_deg = [1, 2]

[ring]
ids = [6, 5]
rest_deg = [-3, 8]

[thumb]
ids = [8, 7]
rest_deg = [8, -8]
"#;

    const LEGACY_SAMPLE: &str = r#"
[Fingers]
[[motors]]
finger_name = "r_finger1"
motor1.id = 1
motor1.offset = 0.12
motor1.invert = false
motor1.model = "SCS0009"
motor2.id = 2
motor2.offset = 0.08
motor2.invert = false
motor2.model = "SCS0009"
[[motors]]
finger_name = "r_finger2"
motor1.id = 3
motor1.offset = 0.0
motor1.invert = false
motor1.model = "SCS0009"
motor2.id = 4
motor2.offset = 0.12
motor2.invert = false
motor2.model = "SCS0009"
[[motors]]
finger_name = "r_finger3"
motor1.id = 5
motor1.offset = 0.08
motor1.invert = false
motor1.model = "SCS0009"
motor2.id = 6
motor2.offset = 0.12
motor2.invert = false
motor2.model = "SCS0009"
[[motors]]
finger_name = "r_finger4"
motor1.id = 7
motor1.offset = 0.0
motor1.invert = false
motor1.model = "SCS0009"
motor2.id = 8
motor2.offset = 0.12
motor2.invert = false
motor2.model = "SCS0009"
"#;

    #[test]
    fn test_is_canonical_format_detects_canonical() {
        assert!(is_canonical_format(CANONICAL_SAMPLE));
    }

    #[test]
    fn test_is_canonical_format_rejects_legacy() {
        assert!(!is_canonical_format(LEGACY_SAMPLE));
    }

    fn parse_canonical_sample(right_hand: bool) -> Fingers {
        let order = default_finger_order();
        parse_canonical_calibration(CANONICAL_SAMPLE, &order, right_hand).unwrap()
    }

    #[test]
    fn test_parse_canonical_produces_four_fingers() {
        let f = parse_canonical_sample(true);
        assert_eq!(f.motors.len(), 4);
    }

    #[test]
    fn test_parse_canonical_finger_names_and_ids() {
        let f = parse_canonical_sample(true);
        assert_eq!(f.motors[0].finger_name, "r_finger1");
        assert_eq!(f.motors[0].motor1.id, 1);
        assert_eq!(f.motors[0].motor2.id, 2);
        assert_eq!(f.motors[3].finger_name, "r_finger4");
        assert_eq!(f.motors[3].motor1.id, 8);
        assert_eq!(f.motors[3].motor2.id, 7);
    }

    #[test]
    fn test_parse_canonical_rest_deg_to_radians() {
        let f = parse_canonical_sample(true);
        let eps = 1e-9;
        assert!((f.motors[0].motor1.offset - (-2.0_f64).to_radians()).abs() < eps);
        assert!((f.motors[0].motor2.offset - 0.0_f64).abs() < eps);
        assert!((f.motors[0].motor1.offset - (-2.0 * std::f64::consts::PI / 180.0)).abs() < eps);
    }

    #[test]
    fn test_load_fingers_from_str_canonical() {
        let f = load_fingers_from_str(CANONICAL_SAMPLE, None).unwrap();
        assert_eq!(f.motors.len(), 4);
        assert_eq!(f.motors[0].motor1.id, 1);
    }

    #[test]
    fn test_load_fingers_from_str_legacy() {
        let f = load_fingers_from_str(LEGACY_SAMPLE, None).unwrap();
        assert_eq!(f.motors.len(), 4);
        assert_eq!(f.motors[0].finger_name, "r_finger1");
        assert_eq!(f.motors[0].motor1.id, 1);
    }

    #[test]
    fn test_parse_canonical_missing_section_fails() {
        let bad = r#"[index]
ids = [1, 2]
rest_deg = [-2, 0]
"#;
        let order = default_finger_order();
        let r = parse_canonical_calibration(bad, &order, true);
        assert!(r.is_err());
        assert!(r.unwrap_err().contains("middle"));
    }
}
