"""LEVEL 4, act B - two factories, one gauge."""

from __future__ import annotations
import math

from manim import *
from msalab.narration import NarratedCameraScene
from msalab.act_style import *
from msalab.against_what import (
    GAUGE_SIGMA, ACCEPT_PCT, REJECT_PCT, NDC_MIN,
    ndc_from_study_ratio, study_ratio_for_ndc, NDC_K
)
from msalab.level04_mastery import challenge_case
from msalab.level04_scene import (
    GAUGE_W, BAND_H, STUDY_Y, TOL_Y, RAIL_Y, 
    _study_shape, _drawing_shape, _measure, _empty_slot, SCALE
)

class Level04Case(NarratedCameraScene):
    def construct(self):
        self.case_A = challenge_case(401)
        self.case_B = challenge_case(402)
        self.case_C = challenge_case(409)

        self.shot01_carry_in()
        self.shot02_factory_A()
        self.shot03_factory_B()
        self.shot04_name_denominator()
        self.shot05_opposite_actions()
        self.shot06_ndc_curve()
        self.shot07_the_chain()

    def _freeze(self, *mobs):
        for m in mobs:
            m.clear_updaters()

    def _home(self):
        return self.camera.frame.width, self.camera.frame.get_center()

    def shot01_carry_in(self):
        """Shot 01: The frame Act A left"""
        # The identical amber gauge band
        self.band = Rectangle(width=GAUGE_W, height=BAND_H, fill_color=ACCENT,
                              fill_opacity=0.85, stroke_color=ACCENT,
                              stroke_width=2.0)
        self.band.move_to([4.30, 2.95, 0]) # Assuming PARK from Act A

        self.add(self.band)

        # Transformation: Act A's readouts leave, band lifted onto a plant rail.
        # A ruler is laid against it.
        rail = Line([-GAUGE_W / 2 - 1.15, RAIL_Y, 0],
                    [GAUGE_W / 2 + 1.15, RAIL_Y, 0],
                    stroke_color=RULE_STRONG, stroke_width=1.6)
        
        # Ruler marks (ticks)
        ruler = VGroup(rail)
        for i in range(7):
            x = -GAUGE_W/2 + i * (GAUGE_W/6)
            tick = Line([x, RAIL_Y - 0.1, 0], [x, RAIL_Y + 0.1, 0], stroke_color=RULE_STRONG)
            ruler.add(tick)

        tag = gauge(f"{GAUGE_SIGMA:.2f} \u03bcm", 22, ACCENT).next_to(self.band, UP, buff=0.2)
        
        with self.say("Same gauge. Nothing has been calibrated, adjusted, or replaced."):
            self.play(
                self.band.animate.move_to([0, RAIL_Y + BAND_H/2, 0]),
                Create(ruler),
                FadeIn(tag, shift=DOWN*0.1),
                run_time=1.5
            )

        # Camera move: slow push to the band and ruler together
        self.play(
            self.camera.frame.animate.scale(0.8).move_to([0, RAIL_Y + BAND_H/2, 0]),
            run_time=2.0
        )
        self.tag = tag
        self.ruler = ruler
        self.beat()

    def shot02_factory_A(self):
        """Shot 02: Factory A: sort what looks the same"""
        # Persistent object: The band unchanged.
        # Transformation: Two part populations appear with spread A_PART.
        
        # A_PART = self.case_A['part_sigma']
        part_sigma = self.case_A['part_sigma']
        job = self.case_A['decision_job']

        # restore camera
        w, c = self._home()
        self.play(
            self.camera.frame.animate.set(width=w).move_to(c),
            FadeOut(self.ruler),
            FadeOut(self.tag),
            self.band.animate.move_to([-3.0, STUDY_Y, 0]),
            run_time=1.5
        )

        job_card_A = prose(f"Decision job = {job}", 22, INK_DIM).to_corner(UL)
        
        # Two populations close together
        pop1 = _study_shape(part_sigma).move_to([-4.0, 0, 0])
        pop2 = _study_shape(part_sigma).move_to([-2.0, 0, 0])
        
        # Bin visual (sorting bin)
        bin_rect = Rectangle(width=6.0, height=2.0, stroke_color=INK_DIM).move_to([-3.0, -2.0, 0])
        bin_text = prose("Sorting Bin", 20, INK_DIM).move_to(bin_rect)

        with self.say("This plant has to put parts in the right bin, and the parts are close together on purpose."):
            self.play(
                FadeIn(job_card_A),
                FadeIn(pop1), FadeIn(pop2),
                FadeIn(bin_rect), FadeIn(bin_text),
                run_time=1.5
            )
        
        self.beat()
        self.job_card_A = job_card_A
        self.pop1 = pop1
        self.pop2 = pop2
        self.bin_group = VGroup(bin_rect, bin_text)

    def shot03_factory_B(self):
        """Shot 03: Factory B: judge against the drawing"""
        job = self.case_B['decision_job']
        b_tol = self.case_B['tolerance']
        b_part = self.case_B['part_sigma']

        job_card_B = prose(f"Decision job = {job}", 22, INK_DIM).to_corner(UR)
        
        pop_b = _study_shape(b_part).move_to([3.0, STUDY_Y, 0])
        limits_b = _drawing_shape(b_tol * SCALE).move_to([3.0, TOL_Y, 0])

        with self.say("This plant does not care which parts differ. It has to say pass or fail against a drawing."):
            self.play(
                self.band.animate.move_to([3.0, TOL_Y, 0]),
                self.bin_group.animate.set_opacity(0.2),
                self.pop1.animate.set_opacity(0.2),
                self.pop2.animate.set_opacity(0.2),
                FadeIn(job_card_B),
                FadeIn(pop_b),
                FadeIn(limits_b),
                run_time=1.5
            )
        
        # Push on boundary crossings
        self.play(
            self.camera.frame.animate.scale(0.8).move_to([3.0, TOL_Y, 0]),
            run_time=1.5
        )
        self.play(
            self.camera.frame.animate.scale(1/0.8).move_to([0, 0, 0]),
            run_time=1.0
        )
        
        self.beat()
        self.job_card_B = job_card_B
        self.pop_b = pop_b
        self.limits_b = limits_b

    def shot04_name_denominator(self):
        """Shot 04: Name the denominator first"""
        w, c = self._home()
        
        # Need two copies of the band, but they are conceptually the same
        band_B = self.band.copy().move_to([3.0, 0.5, 0])
        
        # Fraction skeletons
        bar_A = Line([-3.8, 0, 0], [-2.2, 0, 0], stroke_width=2)
        bar_B = Line([2.2, 0, 0], [3.8, 0, 0], stroke_width=2)
        
        denom_slot_A = prose("??", 24, INK_DIM).move_to([-3.0, -0.5, 0])
        denom_slot_B = prose("??", 24, INK_DIM).move_to([3.0, -0.5, 0])

        with self.say("Before a percentage exists, say what you are dividing by."):
            self.play(
                self.camera.frame.animate.set(width=w).move_to(c),
                self.band.animate.move_to([-3.0, 0.5, 0]),
                FadeIn(band_B),
                FadeIn(bar_A), FadeIn(bar_B),
                FadeIn(denom_slot_A), FadeIn(denom_slot_B),
                self.pop_b.animate.set_opacity(0.2),
                self.limits_b.animate.set_opacity(0.2),
                run_time=1.5
            )
            self.band_A = self.band
            self.band_B = band_B

            # The denominator choices
            den_A = prose("Study variation", 20, INK).move_to([-3.0, -0.5, 0])
            den_B = prose("Tolerance", 20, INK).move_to([3.0, -0.5, 0])
            
            self.play(
                denom_slot_A.animate.become(den_A),
                denom_slot_B.animate.become(den_B),
                run_time=1.5
            )
            
        self.beat()
        self.frac_A_group = VGroup(self.band_A, bar_A, denom_slot_A)
        self.frac_B_group = VGroup(self.band_B, bar_B, denom_slot_B)
        self.den_A = den_A
        self.den_B = den_B

    def shot05_opposite_actions(self):
        """Shot 05: Opposite actions, one instrument"""
        from msalab.level04_mastery import action_for_ratio
        
        with self.say("Both of these are honest. They are answers to different questions."):
            # Fade out the fraction skeletons
            self.play(
                FadeOut(self.frac_A_group),
                FadeOut(self.frac_B_group),
                FadeOut(self.job_card_A),
                FadeOut(self.job_card_B),
                run_time=1.0
            )
            
            # Build grid: Columns are jobs, Rows are factories
            col_1 = prose("sort process populations", 16, INK_DIM).move_to([-3.0, 3.0, 0])
            col_2 = prose("judge drawing conformance", 16, INK_DIM).move_to([3.0, 3.0, 0])
            row_A = prose("Factory A", 16, INK_DIM).move_to([-6.0, 1.0, 0])
            row_B = prose("Factory B", 16, INK_DIM).move_to([-6.0, -1.0, 0])
            
            self.play(FadeIn(col_1), FadeIn(col_2), FadeIn(row_A), FadeIn(row_B))
            
            ratios = {
                "A_study": self.case_A['study_ratio'],
                "A_tol": self.case_A['tolerance_ratio'],
                "B_study": self.case_B['study_ratio'],
                "B_tol": self.case_B['tolerance_ratio'],
            }
            
            cells = []
            for key, pos in [("A_study", [-3.0, 1.0, 0]), ("A_tol", [3.0, 1.0, 0]),
                             ("B_study", [-3.0, -1.0, 0]), ("B_tol", [3.0, -1.0, 0])]:
                ratio = ratios[key]
                action = action_for_ratio(ratio)
                color = SIGNAL_OK if action == "use" else (SIGNAL_ALARM if action == "replace" else INK)
                
                # The action is inside the band. Neutral tile for improve.
                text = prose(f"{ratio:.1f}% -> {action}", 20, color).move_to(pos)
                cells.append(text)
            
            # Show that the band is drawn once and fed into all 4 cells.
            self.play(
                self.band.animate.move_to([0, 1.5, 0]).scale(0.5), # shared numerator
                LaggedStart(*[FadeIn(cell) for cell in cells], lag_ratio=0.2),
                run_time=2.0
            )
            
        self.beat()
        self.grid_elements = VGroup(col_1, col_2, row_A, row_B, self.band, *cells)

    def shot06_ndc_curve(self):
        """Shot 06: ndc is the same curve"""
        with self.say("One of these two printed rules is stricter than the other, and the table they share does not say so."):
            self.play(FadeOut(self.grid_elements), run_time=1.0)
            
            # Draw axes
            ax = Axes(
                x_range=[0, 100, 10],
                y_range=[0, 20, 5],
                x_length=8,
                y_length=5,
                tips=False,
                axis_config={"color": INK_DIM}
            ).move_to([0, 0, 0])
            
            x_label = prose("%GRR_study", 16, INK_DIM).next_to(ax.x_axis, RIGHT)
            y_label = prose("ndc", 16, INK_DIM).next_to(ax.y_axis, UP)
            self.play(Create(ax), FadeIn(x_label), FadeIn(y_label))
            
            # Draw curve from ndc_from_study_ratio
            curve = ax.plot(
                lambda x: ndc_from_study_ratio(x) if 0 < x < 100 else 0,
                color=ACCENT,
                x_range=[1, 99]
            )
            self.play(Create(curve), run_time=1.5)
            
            # Factory points
            pt_a = Dot(ax.coords_to_point(self.case_A['study_ratio'], ndc_from_study_ratio(self.case_A['study_ratio'])), color=SIGNAL_OK)
            pt_b = Dot(ax.coords_to_point(self.case_B['study_ratio'], ndc_from_study_ratio(self.case_B['study_ratio'])), color=SIGNAL_ALARM)
            
            # Printed gates
            accept_line = ax.get_vertical_line(ax.coords_to_point(ACCEPT_PCT, ndc_from_study_ratio(ACCEPT_PCT)), color=SIGNAL_OK)
            ndc_line = ax.get_horizontal_line(ax.coords_to_point(study_ratio_for_ndc(NDC_MIN), NDC_MIN), color=INK)
            reject_line = ax.get_vertical_line(ax.coords_to_point(REJECT_PCT, ndc_from_study_ratio(REJECT_PCT)), color=SIGNAL_ALARM)
            
            self.play(Create(accept_line), Create(reject_line), Create(ndc_line))
            
            # Zoom into the gap between the two gate lines
            self.play(
                self.camera.frame.animate.scale(0.5).move_to(ax.coords_to_point((REJECT_PCT + study_ratio_for_ndc(NDC_MIN))/2, NDC_MIN)),
                run_time=2.0
            )
            
        self.beat()
        self.ndc_group = VGroup(ax, x_label, y_label, curve, pt_a, pt_b, accept_line, reject_line, ndc_line)

    def shot07_the_chain(self):
        """Shot 07: The chain"""
        from msalab.level04_mastery import band_label_for_ratio, action_for_ratio
        
        w, c = self._home()
        self.play(
            self.camera.frame.animate.set(width=w).move_to(c),
            FadeOut(self.ndc_group),
            run_time=1.0
        )
        
        with self.say("The gauge does not own a verdict. The job chooses the denominator, and the denominator carries the rest."):
            # The unchanged band parked
            # Re-create self.band at size/park as we scaled it for grid earlier
            self.band = Rectangle(width=GAUGE_W, height=BAND_H, fill_color=ACCENT,
                                  fill_opacity=0.85, stroke_color=ACCENT,
                                  stroke_width=2.0).move_to([4.30, 2.95, 0])
            self.play(FadeIn(self.band))
            
            # The chain fields (using case_C)
            c_case = self.case_C
            labels = ["Decision job", "Chosen denominator", "Computed %GRR", "AIAG band", "Action"]
            values = [
                c_case['decision_job'],
                c_case['answer']['denominator'],
                f"{c_case['study_ratio'] if c_case['answer']['denominator'] == 'Study variation' else c_case['tolerance_ratio']:.1f}%",
                band_label_for_ratio(c_case['study_ratio'] if c_case['answer']['denominator'] == 'Study variation' else c_case['tolerance_ratio']),
                c_case['answer']['action']
            ]
            
            chain = VGroup()
            for i, (lab, val) in enumerate(zip(labels, values)):
                rect = Rectangle(width=4.0, height=1.2, fill_color=PANEL, fill_opacity=1.0, stroke_color=RULE)
                l_text = panel_label(lab, 14, ACCENT).move_to(rect).shift(UP*0.2)
                v_text = prose(val, 16, INK).move_to(rect).shift(DOWN*0.2)
                if lab == "Action":
                    v_text.set_color(SIGNAL_OK if val == "use" else (SIGNAL_ALARM if val == "replace" else INK))
                
                g = VGroup(rect, l_text, v_text).move_to([-3.0, 3.0 - i*1.4, 0])
                chain.add(g)
                
            # Fly in
            self.play(LaggedStart(*[FadeIn(link, shift=RIGHT) for link in chain], lag_ratio=0.3), run_time=2.5)
            
        self.beat()
