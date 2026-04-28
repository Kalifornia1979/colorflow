#!/usr/bin/env python3
# =============================================================================
# colorflow.py
# Color management dashboard for photographers and video professionals on Linux.
# Run with: python3 colorflow.py
# =============================================================================

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango
import subprocess
import os

# =============================================================================
# CSS
# =============================================================================

CSS = b"""
window {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
.topplinje {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 16px 20px;
}
.tittel {
    font-size: 20px;
    font-weight: bold;
    color: #cdd6f4;
}
.undertittel {
    font-size: 12px;
    color: #6c7086;
}
.hovedstatus-ok {
    background-color: #1e3a2f;
    border: 1px solid #2ecc71;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px;
}
.hovedstatus-advarsel {
    background-color: #3a2e1e;
    border: 1px solid #e67e22;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px;
}
.hovedstatus-tekst-ok {
    font-size: 16px;
    font-weight: bold;
    color: #2ecc71;
}
.hovedstatus-tekst-advarsel {
    font-size: 16px;
    font-weight: bold;
    color: #e67e22;
}
.hovedstatus-detalj {
    font-size: 12px;
    color: #a6adc8;
}
.kort {
    background-color: #252535;
    border: 1px solid #313244;
    border-radius: 8px;
    margin: 6px 16px;
}
.kort-tittel {
    font-size: 14px;
    font-weight: bold;
    color: #cdd6f4;
}
.kort-status-ok {
    font-size: 12px;
    color: #2ecc71;
}
.kort-status-advarsel {
    font-size: 12px;
    color: #e67e22;
}
.kort-status-info {
    font-size: 12px;
    color: #a6adc8;
}
.kort-forklaring {
    font-size: 12px;
    color: #a6adc8;
}
.teknisk-detalj {
    font-size: 11px;
    color: #6c7086;
    font-family: monospace;
}
.knapp-handling {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
}
.knapp-handling:hover {
    background-color: #45475a;
    color: #cdd6f4;
}
.knapp-handling:active {
    background-color: #585b70;
    color: #cdd6f4;
}
.knapp-les-mer {
    background: none;
    border: none;
    color: #7287fd;
    font-size: 11px;
    padding: 0;
}
.knapp-les-mer:hover {
    color: #89b4fa;
}
.oppdater-knapp {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
}
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run(command):
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return (r.stdout + r.stderr).strip()
    except:
        return ""

def has_program(name):
    return subprocess.run(f"command -v {name}", shell=True, capture_output=True).returncode == 0

def get_display_info():
    info = {
        "model": "Unknown display",
        "has_profile": False,
        "profile_count": 0,
        "icc_loaded": False,
        "profile_name": "",
        "has_internal_lut": False,
        "internal_lut_note": ""
    }

    devices = run("colormgr get-devices 2>/dev/null")
    profiles = []
    for line in devices.splitlines():
        line = line.strip()
        if line.startswith("Model"):
            model = line.split(":", 1)[-1].strip()
            if model:
                info["model"] = model
        elif "Profile" in line and "icc-" in line:
            profiles.append(line)

    info["profile_count"] = len(profiles)
    info["has_profile"] = len(profiles) > 0

    icc_prop = run("xprop -display :0 -root _ICC_PROFILE 2>/dev/null")
    info["icc_loaded"] = "_ICC_PROFILE" in icc_prop and len(icc_prop) > 30

    dcal_dir = os.path.expanduser("~/.local/share/DisplayCAL")
    if os.path.isdir(dcal_dir):
        for root, _, files in os.walk(dcal_dir):
            for f in files:
                if f.endswith(".icc") or f.endswith(".icm"):
                    info["profile_name"] = f
                    break

    # Detect displays with internal hardware LUT
    # Check both model name and vendor from colord devices output
    devices_lower = run("colormgr get-devices 2>/dev/null").lower()
    model_lower = info["model"].lower()
    combined = model_lower + " " + devices_lower

    INTERNAL_LUT_DISPLAYS = [
        ("cs240", "Eizo ColorEdge CS240",
         "Your Eizo ColorEdge CS240 has an internal hardware LUT and manages "
         "calibration internally. External LUT loading via dispwin is not needed — "
         "GNOME loads your ICC profile via colord, and the display handles the rest. "
         "If xgamma shows 1.000 for all channels, this is normal and expected."),
        ("cs2731", "Eizo ColorEdge CS2731",
         "Your Eizo ColorEdge CS display has an internal hardware LUT. "
         "External LUT loading is not needed."),
        ("cg", "Eizo ColorEdge CG series",
         "Your Eizo ColorEdge CG display has a built-in 3D LUT and hardware calibration engine. "
         "External LUT loading is not needed."),
        ("nec pa", "NEC MultiSync PA series",
         "Your NEC MultiSync PA display supports hardware calibration with an internal LUT. "
         "External LUT loading via dispwin is typically not needed."),
    ]
    for keyword, label, note in INTERNAL_LUT_DISPLAYS:
        if keyword in combined:
            info["has_internal_lut"] = True
            info["internal_lut_note"] = note
            break

    return info

def get_printer_info():
    info = {"has_printer": False, "printers": [], "has_profiles": False, "profile_source": ""}

    output = run("lpstat -p 2>/dev/null")
    if output and "printer" in output.lower():
        info["has_printer"] = True
        for line in output.splitlines():
            if line.strip():
                info["printers"].append(line.strip())

    for path in ["/usr/share/turboprint", os.path.expanduser("~/.turboprint")]:
        if os.path.isdir(path):
            if run(f"find {path} -name '*.icc' -o -name '*.icm' 2>/dev/null | head -1"):
                info["has_profiles"] = True
                info["profile_source"] = "TurboPrint"

    if run("find /etc/cups /usr/share/cups -name '*.icc' -o -name '*.icm' 2>/dev/null | head -1"):
        info["has_profiles"] = True
        if not info["profile_source"]:
            info["profile_source"] = "CUPS"

    if "cups-" in run("colormgr get-devices 2>/dev/null"):
        info["has_profiles"] = True
        if not info["profile_source"]:
            info["profile_source"] = "colord"

    return info

def get_tools_info():
    return {
        "colormgr": has_program("colormgr"),
        "dispwin": has_program("dispwin"),
        "xcalib": has_program("xcalib"),
        "displaycal": has_program("displaycal"),
        "autostart": os.path.exists(
            os.path.expanduser("~/.config/autostart/z-displaycal-apply-profiles.desktop")
        )
    }

def get_all_profiles():
    """
    Fetches all ICC profiles from colord with readable names (Title field).
    Returns two lists: relevant (display/printer) and system profiles.
    """
    output = run("colormgr get-profiles 2>/dev/null")

    SYSTEM_DIRS = [
        "/usr/share/color/icc/colord/",
        "/usr/share/color/icc/ghostscript/",
    ]

    RELEVANT_KEYWORDS = [
        "cs240", "eizo", "edid", "luster", "lustre",
        "surecolor", "turboprint", "epson", "p800",
        "prophoto", "adobe", "srgb", "display",
        "displaycal", "xyzlut", "nanao"
    ]

    relevant = []
    system = []
    current = {}

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Object Path"):
            # Object Path signals a new profile block — save current and start fresh
            if current and current.get("id"):
                _categorize_profile(current, SYSTEM_DIRS, RELEVANT_KEYWORDS, relevant, system)
            current = {"id": "", "filename": "", "title": "", "name": ""}
        elif line.startswith("Profile ID"):
            if current and current.get("id"):
                _categorize_profile(current, SYSTEM_DIRS, RELEVANT_KEYWORDS, relevant, system)
                current = {"id": "", "filename": "", "title": "", "name": ""}
            current["id"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Filename"):
            current["filename"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Title"):
            current["title"] = line.split(":", 1)[-1].strip()

    if current:
        _categorize_profile(current, SYSTEM_DIRS, RELEVANT_KEYWORDS, relevant, system)

    # For profiles still missing title or filename, fetch individually
    # Also use this to filter out ghost registrations (no output = dead profile)
    dead_ids = set()
    all_profiles = relevant + system
    for p in all_profiles:
        needs_detail = not p["title"] or not p["filename"]
        if needs_detail and p.get("id"):
            detail = run(f"colormgr find-profile {p['id']} 2>/dev/null")
            if not detail.strip():
                dead_ids.add(p["id"])
                continue
            for line in detail.splitlines():
                line = line.strip()
                if line.startswith("Title") and not p["title"]:
                    p["title"] = line.split(":", 1)[-1].strip()
                elif line.startswith("Filename") and not p["filename"]:
                    val = line.split(":", 1)[-1].strip()
                    if not val.startswith("Metadata"):
                        p["filename"] = val
            if not p["title"] and not p["filename"]:
                p["title"] = p.get("id", "")
        # Prefer title as display name, but only if name not already set by categorizer
        if p["title"] and not p.get("name"):
            p["name"] = p["title"]
        elif p["title"] and p.get("name") == p.get("id", ""):
            # name was set to raw ID — replace with title
            p["name"] = p["title"]

    # Re-categorize profiles that now have a filename but were put in wrong bucket
    final_relevant = []
    final_system = []
    for p in relevant + system:
        if p.get("id", "") in dead_ids:
            continue
        filename = p.get("filename", "")
        in_system_dir = any(filename.startswith(d) for d in SYSTEM_DIRS)
        if in_system_dir:
            final_system.append(p)
        elif p in relevant:
            final_relevant.append(p)
        else:
            final_system.append(p)
    relevant, system = final_relevant, final_system

    # Remove dead profiles
    relevant = [p for p in relevant if p.get("id", "") not in dead_ids]
    system = [p for p in system if p.get("id", "") not in dead_ids]

    # Remove duplicates by name, keeping first occurrence
    seen = set()
    relevant = [p for p in relevant if not (p["name"] in seen or seen.add(p["name"]))]
    system = [p for p in system if not (p["name"] in seen or seen.add(p["name"]))]

    return relevant, system

def _categorize_profile(profile, system_dirs, relevant_keywords, relevant, system):
    """Sorts a profile into relevant or system list, using Title as display name."""
    filename = profile.get("filename", "")
    title = profile.get("title", "")
    pid = profile.get("id", "")

    # Use Title if available, otherwise filename stem, otherwise ID
    if title:
        profile["name"] = title
    elif filename:
        profile["name"] = os.path.splitext(os.path.basename(filename))[0]
    else:
        profile["name"] = pid

    # No filename = TurboPrint or similar — treat as relevant
    if not filename:
        pid = profile.get("id", "")
        if "TurboPrint" in pid:
            # Parse: PrinterModel-TurboPrint-Colorspace..
            # e.g. SureColorP800-TurboPrint-RGB.. -> SureColor P800 — TurboPrint (RGB)
            parts = pid.split("-TurboPrint-")
            printer_part = parts[0] if parts else pid
            colorspace_part = parts[1].rstrip(".") if len(parts) > 1 else ""

            # Clean up printer name — replace hyphens with spaces
            printer_readable = printer_part.replace("-", " ").strip()

            if colorspace_part:
                profile["name"] = f"{printer_readable} — TurboPrint ({colorspace_part})"
            else:
                profile["name"] = f"{printer_readable} — TurboPrint"
        relevant.append(profile)
        return

    # System directory = system profile
    for d in system_dirs:
        if filename.startswith(d):
            system.append(profile)
            return

    # Check name and title against relevant keywords
    search = (profile["name"] + " " + filename).lower()
    for kw in relevant_keywords:
        if kw in search:
            relevant.append(profile)
            return

    # Default: system
    system.append(profile)

def count_warnings(display, printer, tools):
    n = 0
    if not display["icc_loaded"]:
        n += 1
    if not printer["has_printer"] or not printer["has_profiles"]:
        n += 1
    if not tools["colormgr"]:
        n += 1
    return n

# =============================================================================
# CARD COMPONENT
# =============================================================================

class InfoCard(Gtk.Box):
    def __init__(self, icon, title, status_text, status_ok, explanation, technical="", actions=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("kort")

        # Store data for dynamic rendering
        self.explanation = explanation
        self.technical = technical
        self.actions = actions or []
        self.expanded = False

        # Top row
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top.set_margin_top(14)
        top.set_margin_bottom(10)
        top.set_margin_start(16)
        top.set_margin_end(16)

        icon_label = Gtk.Label()
        icon_label.set_markup(f'<span size="x-large">{icon}</span>')
        top.pack_start(icon_label, False, False, 0)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0)
        title_label.get_style_context().add_class("kort-tittel")
        text_box.pack_start(title_label, False, False, 0)

        status_label = Gtk.Label(label=status_text)
        status_label.set_xalign(0)
        status_label.get_style_context().add_class(
            "kort-status-ok" if status_ok is True else
            "kort-status-advarsel" if status_ok is False else
            "kort-status-info"
        )
        text_box.pack_start(status_label, False, False, 0)

        top.pack_start(text_box, True, True, 0)

        self.more_btn = Gtk.Button(label="More ▾")
        self.more_btn.get_style_context().add_class("knapp-les-mer")
        self.more_btn.set_valign(Gtk.Align.START)
        self.more_btn.connect("clicked", self.toggle_details)
        top.pack_end(self.more_btn, False, False, 0)

        self.pack_start(top, False, False, 0)

        # Empty container for detail content
        self.detail_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.detail_panel.set_margin_start(16)
        self.detail_panel.set_margin_end(16)
        self.detail_panel.set_margin_bottom(14)
        self.pack_start(self.detail_panel, False, False, 0)

    def toggle_details(self, widget):
        self.expanded = not self.expanded

        # Always clear first
        for child in self.detail_panel.get_children():
            self.detail_panel.remove(child)

        if self.expanded:
            self.more_btn.set_label("Close ▴")

            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.set_margin_bottom(8)
            self.detail_panel.pack_start(sep, False, False, 0)

            if self.explanation:
                expl = Gtk.Label(label=self.explanation)
                expl.set_xalign(0)
                expl.set_line_wrap(True)
                expl.set_line_wrap_mode(Pango.WrapMode.WORD)
                expl.get_style_context().add_class("kort-forklaring")
                self.detail_panel.pack_start(expl, False, False, 0)

            if self.technical:
                tech = Gtk.Label(label=self.technical)
                tech.set_xalign(0)
                tech.set_line_wrap(True)
                tech.set_line_wrap_mode(Pango.WrapMode.WORD)
                tech.get_style_context().add_class("teknisk-detalj")
                tech.set_margin_top(8)
                self.detail_panel.pack_start(tech, False, False, 0)

            if self.actions:
                btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                btn_row.set_margin_top(10)
                for (lbl, callback) in self.actions:
                    btn = Gtk.Button(label=lbl)
                    # Inject CSS directly on this widget to override GTK theme
                    btn_css = Gtk.CssProvider()
                    btn_css.load_from_data(b"""
                        button {
                            background: #313244;
                            background-image: none;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            border-radius: 6px;
                            padding: 4px 12px;
                            font-size: 12px;
                            box-shadow: none;
                        }
                        button:hover {
                            background: #45475a;
                            background-image: none;
                            color: #cdd6f4;
                        }
                    """)
                    btn.get_style_context().add_provider(
                        btn_css, Gtk.STYLE_PROVIDER_PRIORITY_USER
                    )
                    btn.connect("clicked", callback)
                    btn_row.pack_start(btn, False, False, 0)
                self.detail_panel.pack_start(btn_row, False, False, 0)

            self.detail_panel.show_all()

        else:
            self.more_btn.set_label("More ▾")

# =============================================================================
# MAIN WINDOW
# =============================================================================

class ColorFlow(Gtk.Window):
    def __init__(self):
        super().__init__(title="ColorFlow")
        self.set_default_size(680, 720)
        self.set_border_width(0)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(outer)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("topplinje")

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label="ColorFlow")
        title_label.set_xalign(0)
        title_label.get_style_context().add_class("tittel")
        title_box.pack_start(title_label, False, False, 0)

        sub_label = Gtk.Label(label="Color management overview for photographers and video professionals")
        sub_label.set_xalign(0)
        sub_label.get_style_context().add_class("undertittel")
        title_box.pack_start(sub_label, False, False, 0)

        header.pack_start(title_box, True, True, 0)

        refresh_btn = Gtk.Button(label="↻  Refresh")
        refresh_btn.get_style_context().add_class("oppdater-knapp")
        refresh_btn.set_valign(Gtk.Align.CENTER)
        refresh_btn.connect("clicked", self.refresh)
        header.pack_end(refresh_btn, False, False, 0)

        outer.pack_start(header, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        outer.pack_start(scroll, True, True, 0)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        scroll.add(self.content)

        self.refresh(None)
        self.show_all()

    def refresh(self, widget):
        for child in self.content.get_children():
            self.content.remove(child)

        display = get_display_info()
        printer = get_printer_info()
        tools = get_tools_info()
        warnings = count_warnings(display, printer, tools)

        # Main status banner
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        if warnings == 0:
            banner.get_style_context().add_class("hovedstatus-ok")
            icon, text, detail, css = (
                "✓",
                "Color flow OK — you're ready to work",
                "Your display and printer are calibrated and ready for color-critical work.",
                "hovedstatus-tekst-ok"
            )
        else:
            banner.get_style_context().add_class("hovedstatus-advarsel")
            icon, text, detail, css = (
                "⚠",
                f"{warnings} item{'s' if warnings > 1 else ''} need attention",
                "See the cards below for explanations and suggested actions.",
                "hovedstatus-tekst-advarsel"
            )

        icon_label = Gtk.Label()
        icon_label.set_markup(f'<span size="xx-large">{icon}</span>')
        banner.pack_start(icon_label, False, False, 0)

        banner_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        b1 = Gtk.Label(label=text)
        b1.set_xalign(0)
        b1.get_style_context().add_class(css)
        banner_text.pack_start(b1, False, False, 0)

        b2 = Gtk.Label(label=detail)
        b2.set_xalign(0)
        b2.get_style_context().add_class("hovedstatus-detalj")
        banner_text.pack_start(b2, False, False, 0)
        banner.pack_start(banner_text, True, True, 0)

        self.content.pack_start(banner, False, False, 0)

        # Display card
        if display["icc_loaded"]:
            d_status, d_ok = "✓ Calibrated and ready", True
            d_expl = (
                f"Your display ({display['model']}) is calibrated and the ICC profile is loaded. "
                "This means the colors you see in your image editor are as accurate as possible, "
                "and screen-to-print matching is working correctly."
            )
        else:
            d_status, d_ok = "⚠ ICC profile not confirmed loaded", False
            d_expl = (
                "No active ICC profile was found in display memory. "
                "This may mean your display is not calibrated, which can cause the colors "
                "you see on screen to differ from your printed output. "
                "Open DisplayCAL and verify that your profile loads at startup."
            )

        d_tech = (
            f"Model: {display['model']}\n"
            f"Profiles in colord: {display['profile_count']}\n"
            f"ICC loaded in X11: {'Yes' if display['icc_loaded'] else 'No'}\n"
            f"Calibration file: {display['profile_name'] or 'Not found'}"
        )

        # Add internal LUT note if relevant
        if display["has_internal_lut"]:
            d_tech += f"\n\nNote: {display['internal_lut_note']}"
        elif not display["icc_loaded"]:
            d_tech += (
                "\n\nNote: If xgamma shows 1.000 for all channels, the calibration curve "
                "(LUT) may not be loaded. This can affect color accuracy. "
                "Use the 'Copy calibration load command' button below and run it in a terminal."
            )

        d_actions = []
        if has_program("displaycal"):
            d_actions.append(("Open DisplayCAL", self.open_displaycal))
        if has_program("dispwin"):
            d_actions.append(("Copy calibration load command", self.copy_dispwin_command))

        self.content.pack_start(InfoCard(
            icon="🖥", title="Display",
            status_text=d_status, status_ok=d_ok,
            explanation=d_expl, technical=d_tech,
            actions=d_actions or None
        ), False, False, 0)

        # Printer card
        if not printer["has_printer"]:
            p_status, p_ok = "⚠ No printer found", False
            p_expl = (
                "No printer was detected on this system. "
                "Make sure your printer is connected and that CUPS is installed."
            )
        elif not printer["has_profiles"]:
            p_status, p_ok = "⚠ No ICC profiles found for printer", False
            p_expl = (
                "Your printer is registered, but no ICC profiles were found for it. "
                "Without a printer profile, colors in your prints will not match what you see on screen. "
                "Download ICC profiles from your paper manufacturer's website, "
                "or use TurboPrint which manages profiles automatically."
            )
        else:
            p_status = f"✓ Ready — profiles via {printer['profile_source']}"
            p_ok = True
            p_expl = (
                "Your printer is registered and ICC profiles are available. "
                "Tip: always select the correct paper profile in your image editor before printing, "
                "and disable color management in the printer dialog to avoid double correction."
            )

        self.content.pack_start(InfoCard(
            icon="🖨", title="Printer",
            status_text=p_status, status_ok=p_ok,
            explanation=p_expl,
            technical="\n".join(printer["printers"]) if printer["printers"] else ""
        ), False, False, 0)

        # Tools card
        all_ok = tools["colormgr"] and tools["dispwin"]
        if all_ok:
            t_status, t_ok = "✓ All required tools are installed", True
            t_expl = (
                "All necessary color management tools are in place. "
                "colord manages ICC profiles automatically, and GNOME loads them at login."
            )
        else:
            missing = [v for v in ["colormgr", "dispwin"] if not tools[v]]
            t_status = f"⚠ Missing: {', '.join(missing)}"
            t_ok = False
            t_expl = (
                f"Some tools are missing ({', '.join(missing)}). "
                "These are used to load and verify color profiles on your system."
            )

        t_tech = (
            f"colormgr:  {'✓' if tools['colormgr'] else '✗'}\n"
            f"dispwin:   {'✓' if tools['dispwin'] else '✗'}\n"
            f"xcalib:    {'✓' if tools['xcalib'] else '✗'}\n"
            f"DisplayCAL autostart: {'✓' if tools['autostart'] else '— (GNOME loads profile via colord)'}"
        )

        t_actions = []
        if not all_ok:
            t_actions.append(("Copy install command", self.show_install))

        self.content.pack_start(InfoCard(
            icon="⚙", title="Software & Tools",
            status_text=t_status, status_ok=t_ok,
            explanation=t_expl, technical=t_tech,
            actions=t_actions or None
        ), False, False, 0)

        # ICC Profiles card
        relevant_profiles, system_profiles = get_all_profiles()

        if relevant_profiles:
            prof_status = f"✓ {len(relevant_profiles)} profile{'s' if len(relevant_profiles) > 1 else ''} active"
            prof_ok = True
            prof_expl = (
                "These are the ICC profiles relevant to your color workflow — "
                "your display calibration, paper profiles, and printer profiles."
            )
        else:
            prof_status = "⚠ No relevant profiles found"
            prof_ok = False
            prof_expl = (
                "No display or printer profiles were found. "
                "Make sure DisplayCAL has created a calibration profile for your display, "
                "and that paper profiles are installed for your printer."
            )

        # Build readable profile list
        relevant_lines = "\n".join(
            f"  • {p['name']}" for p in relevant_profiles if p["name"]
        )
        system_lines = "\n".join(
            f"  • {p['name']}" for p in system_profiles if p["name"]
        )

        prof_tech = ""
        if relevant_lines:
            prof_tech += f"Your profiles:\n{relevant_lines}"
        if system_lines:
            prof_tech += f"\n\nSystem profiles ({len(system_profiles)} total — installed with colord):\n{system_lines}"

        self.content.pack_start(InfoCard(
            icon="🎨", title="ICC Profiles",
            status_text=prof_status, status_ok=prof_ok,
            explanation=prof_expl,
            technical=prof_tech.strip()
        ), False, False, 0)

        # Wine card
        wine_installed = has_program("wine")
        wine_apps = []

        wine_locations = [
            ("PhotoLine", "~/.wine/drive_c/Program Files/PhotoLine"),
            ("PhotoLine", "~/.wine/drive_c/Program Files (x86)/PhotoLine"),
            ("GIMP", "~/.wine/drive_c/Program Files/GIMP 2"),
            ("GIMP", "~/.wine/drive_c/Program Files (x86)/GIMP 2"),
            ("Photoshop", "~/.wine/drive_c/Program Files/Adobe/Photoshop"),
            ("Photoshop", "~/.wine/drive_c/Program Files (x86)/Adobe/Photoshop"),
            ("Lightroom", "~/.wine/drive_c/Program Files/Adobe/Lightroom"),
            ("Capture One", "~/.wine/drive_c/Program Files/Capture One"),
        ]
        for app_name, path in wine_locations:
            if os.path.isdir(os.path.expanduser(path)):
                wine_apps.append(app_name)

        wine_icc = []
        wine_icc_path = os.path.expanduser("~/.wine")
        if os.path.isdir(wine_icc_path):
            result = subprocess.run(
                f"find {wine_icc_path} -name '*.icc' -o -name '*.icm' 2>/dev/null | head -5",
                shell=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                wine_icc = [os.path.basename(f) for f in result.stdout.strip().splitlines()]

        if not wine_installed:
            w_status = "Wine is not installed"
            w_expl = (
                "Wine is not installed on this system, so this section does not apply to you. "
                "If you ever install Windows image editors via Wine, return here for guidance "
                "on color management."
            )
            w_tech = ""
        else:
            detected = f" — {', '.join(set(wine_apps))} detected" if wine_apps else ""
            w_status = f"ℹ Wine is installed{detected}"
            w_expl = (
                "This section is only relevant if you use image editing or printing applications "
                "running inside Wine.\n\n"
                "If you do: both Wine and Linux can apply color correction at the same time, "
                "which causes colors to be corrected twice and makes prints look wrong. "
                "To avoid this, you need to configure color management inside your Wine application manually.\n\n"
                "ColorFlow cannot check this for you — it is something you need to verify yourself."
            )
            w_tech = ""
            if wine_apps:
                app_list = ', '.join(set(wine_apps))
                w_tech += f"For {app_list} via Wine:\n"
                w_tech += (
                    "  Open the application's color management settings\n"
                    "  • Working color space: keep your preferred space (e.g. AdobeRGB)\n"
                    "  • Monitor/display profile: disable or set to sRGB — let Linux handle display correction\n"
                    "  • Printer profile: keep your paper ICC profile active\n\n"
                )
            w_tech += (
                "How to verify your setup is correct:\n"
                "  Print a test image with known colors and compare it to your screen.\n"
                "  This is something you must do yourself — no software can do it for you.\n"
                "  If colors match: your setup is correct.\n"
                "  If colors look off: check that display color management is not active in both "
                "Linux and your Wine application at the same time."
            )
            if wine_icc:
                w_tech += "\n\nICC profiles found inside Wine:\n"
                w_tech += "\n".join(f"  • {f}" for f in wine_icc)
                # Check if printer profiles are among the Wine ICC files
                printer_profiles = [f for f in wine_icc if any(
                    kw in f.lower() for kw in ["luster", "lustre", "matte", "glossy", "paper", "epson", "canon", "hp"]
                )]
                if printer_profiles:
                    w_tech += (
                        "\n\n  Your Wine application has its own copies of printer profiles. "
                        "This means printer color correction is handled inside the Wine app — "
                        "double correction on the printer side is not a concern. "
                        "Focus on disabling display color management only."
                    )

        self.content.pack_start(InfoCard(
            icon="🍷", title="Wine Applications",
            status_text=w_status, status_ok=None,
            explanation=w_expl,
            technical=w_tech
        ), False, False, 0)

        # Tips card
        self.content.pack_start(InfoCard(
            icon="💡", title="Tips for accurate screen-to-print results",
            status_text="Best practices for color work",
            status_ok=True,
            explanation=(
                "1. Recalibrate your display with DisplayCAL at least once a month — "
                "displays drift over time.\n\n"
                "2. Enable color management in all applications: in GIMP go to "
                "Edit → Color Management. In Darktable it is enabled by default.\n\n"
                "3. Always select the correct paper profile when printing — "
                "different paper types reproduce colors differently.\n\n"
                "4. Disable the printer's own color correction when printing from "
                "color-managed applications — otherwise colors will be corrected twice.\n\n"
                "5. Let your display warm up for 20–30 minutes before critical color work."
            )
        ), False, False, 0)

        bottom = Gtk.Box()
        bottom.set_margin_bottom(16)
        self.content.pack_start(bottom, False, False, 0)

        self.content.show_all()

    def open_displaycal(self, widget):
        try:
            subprocess.Popen(["displaycal"])
        except:
            self.show_dialog(
                "Could not open DisplayCAL",
                "Try running 'displaycal' in a terminal to see the error message."
            )

    def copy_to_clipboard(self, widget, text):
        """Copies a command to clipboard and confirms to the user."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()
        self.show_dialog(
            "✓ Copied to clipboard",
            f"Paste and run this in a terminal:\n\n{text}"
        )

    def show_install(self, widget):
        self.copy_to_clipboard(
            widget,
            "sudo apt install argyll"
        )

    def copy_dispwin_command(self, widget):
        """Finds the calibration file and copies the load command."""
        dcal_dir = os.path.expanduser("~/.local/share/DisplayCAL")
        cal_file = None
        for root, _, files in os.walk(dcal_dir):
            for f in files:
                if f.endswith(".cal"):
                    cal_file = os.path.join(root, f)
                    break
        if cal_file:
            cmd = f'dispwin -d 1 "{cal_file}"'
            self.copy_to_clipboard(widget, cmd)
        else:
            self.show_dialog(
                "Calibration file not found",
                "No .cal file was found in your DisplayCAL folder.\n"
                "Make sure you have calibrated your display with DisplayCAL first."
            )

    def show_dialog(self, title, text):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    app = ColorFlow()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()
