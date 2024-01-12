import json
import os
import shutil
import subprocess

import parse_mk_config

import ray
from ray.air import session, RunConfig
from ray import tune
from ray.tune.search import ConcurrencyLimiter
from ray.tune.search.optuna import OptunaSearch


class chateda:
    def __init__(self) -> None:
        """User Guide: Any steps in follows can't be executed unless the previous step has been executed. The usual flow of chip designing goes like this in sequence: a. Setup; b. Synthesis; c. Floorplanning; d. Placement; e. Clock Tree Synthesis (CTS); f. Global Routing; g. Detailed Routing; h. Density Fill; i. Final Report; 
        """

        self.ord = subprocess.Popen(
            "openroad", stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self.time_cmd = "/usr/bin/time -f 'Elapsed time: %E[h:]min:sec. CPU time: user %U sys %S (%P). Peak memory: %MKB.'"
        self.yosys_cmd = "yosys"
        self.yosys_flags = "-v 3"
        self.ord_cmd = "openroad -exit -no_init"

        print("init done")

    def help(self) -> None:
        outs, _ = self.ord.communicate(b"help")
        self._print(outs)

    def _print(self, outs) -> None:
        print("".join(outs.decode().splitlines(keepends=True)[:-1]), flush=True)

    # Setup
    def setup(
        self,
        design_name: str,
        platform: str,
        flow_home: str = ".",
        verilog: str = None,
        sdc: str = None,
    ) -> None:
        """Setup EDA tool.
        Keyword parameters:
            design_name(str) -- The name of the top-level module of the design.
            platform(str) -- Specifies process design kit or technology node to be used. Supported options are "asap7", "nangate45", "sky130", and "gf180".
            flow_home(str) -- The path to the flow home directory.
            verilog(str) -- The path to the design Verilog files.
            sdc(str) --  The path to design constraint (SDC) file.
        """

        os.environ["DESIGN_NAME"] = (
            "aes_cipher_top" if design_name == "aes" else design_name
        )
        os.environ["PLATFORM"] = platform
        if verilog is None:
            verilog = os.path.join(
                flow_home, "designs/src/", design_name, design_name + ".v"
            )
        if sdc is None:
            sdc = os.path.join(
                flow_home, "./designs/", platform, design_name, "constraint.sdc"
            )
        os.environ["VERILOG_FILES"] = verilog
        os.environ["SDC_FILE"] = sdc

        os.environ["FLOW_HOME"] = flow_home
        os.environ["DESIGN_HOME"] = os.path.join(flow_home, "designs")
        os.environ["PLATFORM_HOME"] = os.path.join(flow_home, "platforms")
        os.environ["WORK_HOME"] = flow_home

        os.environ["UTILS_DIR"] = os.path.join(flow_home, "util")
        os.environ["SCRIPTS_DIR"] = os.path.join(flow_home, "scripts")
        os.environ["TEST_DIR"] = os.path.join(flow_home, "test")
        os.environ["PLATFORM_DIR"] = os.path.join(os.environ["PLATFORM_HOME"], platform)

        # parse design config first, because parse_mk_config ignores
        # those already defined env vars
        design_config = parse_mk_config.parse(
            os.path.join(os.environ["DESIGN_HOME"], platform, design_name, "config.mk")
        )
        for k, v in design_config.items():
            os.environ[k] = v

        platform_config = parse_mk_config.parse(
            os.path.join(os.environ["PLATFORM_DIR"], "config.mk")
        )
        for k, v in platform_config.items():
            os.environ[k] = v

        default_env_vars = {
            "GALLERY_REPORT": "0",
            # Enables hierarchical yosys
            "SYNTH_HIERARCHICAL": "0",
            "RESYNTH_AREA_RECOVER": "0",
            "RESYNTH_TIMING_RECOVER": "0",
            "ABC_AREA": "0",
            "SYNTH_ARGS": "-flatten",
            # Global setting for Floorplan
            "PLACE_PINS_ARGS": "",
            "FLOW_VARIANT": "base",
            "GPL_TIMING_DRIVEN": "1",
            "GPL_ROUTABILITY_DRIVEN": "1",
            "ENABLE_DPO": "1",
            "DPO_MAX_DISPLACEMENT": "5 1",
            # Setup working directories
            "DESIGN_NICKNAME": "$(DESIGN_NAME)",
        }
        for k, v in default_env_vars.items():
            if k not in os.environ:
                os.environ[k] = v

        os.environ["DESIGN_DIR"] = os.path.join(
            flow_home, "designs", platform, design_name
        )
        os.environ["LOG_DIR"] = os.path.join(
            flow_home, "logs", platform, design_name, os.environ["FLOW_VARIANT"]
        )
        os.environ["OBJECTS_DIR"] = os.path.join(
            flow_home, "objects", platform, design_name, os.environ["FLOW_VARIANT"]
        )
        os.environ["REPORTS_DIR"] = os.path.join(
            flow_home, "reports", platform, design_name, os.environ["FLOW_VARIANT"]
        )
        os.environ["RESULTS_DIR"] = os.path.join(
            flow_home, "results", platform, design_name, os.environ["FLOW_VARIANT"]
        )

        shutil.rmtree(os.path.join(os.environ["OBJECTS_DIR"], "2*"), ignore_errors=True)
        shutil.rmtree(os.path.join(os.environ["OBJECTS_DIR"], "3*"), ignore_errors=True)
        shutil.rmtree(os.path.join(os.environ["OBJECTS_DIR"], "4*"), ignore_errors=True)
        shutil.rmtree(os.path.join(os.environ["OBJECTS_DIR"], "5*"), ignore_errors=True)
        shutil.rmtree(os.path.join(os.environ["OBJECTS_DIR"], "6*"), ignore_errors=True)

        os.environ["SYNTH_STOP_MODULE_SCRIPT"] = os.path.join(
            os.environ["OBJECTS_DIR"], "mark_hier_stop_modules.tcl"
        )
        if os.environ["SYNTH_HIERARCHICAL"] == "1":
            os.environ["HIER_REPORT_SCRIPT"] = os.path.join(
                os.environ["SCRIPTS_DIR"], "synth_hier_report.tcl"
            )
            if "MAX_UNGROUP_SIZE" not in os.environ:
                os.environ["MAX_UNGROUP_SIZE"] = "0"

        os.environ["NUM_CORES"] = str(os.cpu_count())

        wrapped_lefs = [
            os.path.join(
                "$(OBJECTS_DIR)/lef",
                os.path.splitext(os.path.basename(lef))[0] + "_mod.lef",
            )
            for lef in os.environ.get("WRAP_LEFS", "").split()
            if lef
        ]
        wrapped_libs = [
            os.path.join(
                "$(OBJECTS_DIR)",
                os.path.splitext(os.path.basename(lib))[0] + "_mod.lib",
            )
            for lib in os.environ.get("WRAP_LIBS", "").split()
            if lib
        ]
        os.environ["ADDITIONAL_LEFS"] = " ".join(
            os.environ.get("ADDITIONAL_LEFS", "").split()
            + wrapped_lefs
            + os.environ.get("WRAP_LEFS", "").split()
        )
        os.environ["LIB_FILES"] = " ".join(
            os.environ.get("LIB_FILES", "").split()
            + os.environ.get("WRAP_LIBS", "").split()
            + wrapped_libs
        )
        dont_use_libs = [
            os.path.join(
                os.environ["OBJECTS_DIR"],
                "lib",
                os.path.splitext(os.path.basename(lib))[0] + ".lib",
            )
            for lib in os.environ["LIB_FILES"].split()
        ]
        dont_use_sc_lib = dont_use_libs[0] if dont_use_libs else None
        os.environ["DONT_USE_LIBS"] = " ".join(dont_use_libs)
        os.environ["DONT_USE_SC_LIB"] = dont_use_sc_lib if dont_use_sc_lib else ""

        # Create temporary Liberty files which have the proper dont_use properties set
        # For use with Yosys and ABC
        os.makedirs(os.path.join(os.environ["OBJECTS_DIR"], "lib"), exist_ok=True)
        dont_use_cells = os.environ["DONT_USE_CELLS"]
        dont_use_libs = os.environ["DONT_USE_LIBS"].split()
        for f in os.environ["LIB_FILES"].split():
            f_base = os.path.basename(f)
            for dont_use in dont_use_libs:
                dont_use_base = os.path.basename(dont_use)
                if f_base == dont_use_base or f_base + ".gz" == dont_use_base:
                    cmd = f"{os.path.join(os.environ['UTILS_DIR'], 'markDontUse.py')} -p '{dont_use_cells}' -i {f} -o {dont_use}"
                    print(cmd)
                    subprocess.run(cmd, shell=True)

        print("setup done")

    # Synthesis
    def run_synthesis(self, clock_period: int = None, abc_area: bool = False):
        """Run logic synthesis.
        Logic synthesis can't be executed without setting up.
        Keyword parameters:
            clock_period(int) -- Clock period to be used by STA during synthesis. Default value read from constraint.sdc
            abc_area(bool) -- Strategies for Yosys ABC synthesis: Area/Speed. Default ABC_SPEED.
        """

        if clock_period is not None:
            os.environ["ABC_CLOCK_PERIOD_IN_PS"] = str(clock_period)
            with open(os.environ["DESIGN_DIR"] + "/constraint.sdc", "r") as f:
                lines = f.readlines()
            with open(os.environ["DESIGN_DIR"] + "/constraint.sdc", "w") as new_f:
                for line in lines:
                    if "set clk_period" in line:
                        new_f.write(f"set clk_period {clock_period}\n")
                    else:
                        new_f.write(line)
        os.environ["ABC_AREA"] = "1" if abc_area else "0"
        synth_script = os.path.join(os.environ["SCRIPTS_DIR"], "synth.tcl")
        results_dir = os.environ["RESULTS_DIR"]
        log_dir = os.environ["LOG_DIR"]
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.environ["REPORTS_DIR"], exist_ok=True)

        if os.environ["SYNTH_HIERARCHICAL"] == "1":
            yosys_cmd = " ".join(
                [
                    self.yosys_cmd,
                    self.yosys_flags,
                    "-c " + os.environ["HIER_REPORT_SCRIPT"],
                ]
            )
            cmd = self.time_cmd + " " + yosys_cmd

            with open(
                os.path.join(log_dir, "1_1_yosys_hier_report.log"), "w"
            ) as log_file:
                subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT)

        cmd = " ".join(
            [self.time_cmd, self.yosys_cmd, self.yosys_flags, "-c " + synth_script]
        )
        print(cmd)
        with open(os.path.join(log_dir, "1_1_yosys.log"), "w") as log_file:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
            )
            self._print(result.stdout)
            log_file.write(result.stdout.decode())

        shutil.copy(
            os.path.join(results_dir, "1_1_yosys.v"),
            os.path.join(results_dir, "1_synth.v"),
        )

        shutil.copy(os.environ["SDC_FILE"], os.path.join(results_dir, "1_synth.sdc"))
        
        print("run_synthesis done")

    # Floorplan
    def floorplan(
        self,
        netlist: str = None,
        core_utilization: float = None,
        core_aspect_ratio: float = None,
        core_margins: int = None,
        macro_place_halo: int = None,
        macro_place_channel: int = None,
    ):
        """Run floorplan.
        Floorplan can't be executed without logic synthesis.
        Keyword parameters:
            netlist(str) -- Path to gate-level netlist. If it's set to None, the gate-level netlist file will be read in the default path.
            core_utilization(float) --The core utilization percentage (0-100).
            core_aspect_ratio(float) -- The core aspect ratio (height / width).
            core_margins(int) -- The margin between the core area and die area, in multiples of SITE heights. The margin is applied to each side.
            macro_place_halo(int) -- horizontal/vertical halo around macros (microns). Used by automatic macro placement.
            macro_place_channel(int) -- horizontal/vertical channel width between macros (microns). Used by automatic macro placement when RTLMP_FLOW is disabled. Imagine channel=10 and halo=5. Then macros must be 10 apart but standard cells must be 5 away from a macro.
        """

        if core_utilization is not None:
            os.environ["CORE_UTILIZATION"] = str(core_utilization)
            if core_aspect_ratio is not None:
                os.environ["CORE_ASPECT_RATIO"] = str(core_aspect_ratio)
            if core_margins is not None:
                os.environ["CORE_MARGINS"] = str(core_margins)
        if macro_place_halo is not None:
            os.environ["MACRO_PLACE_HALO"] = str(macro_place_halo)
        if macro_place_channel is not None:
            os.environ["MACRO_PLACE_CHANNEL"] = str(macro_place_channel)
        results_dir = os.environ["RESULTS_DIR"]

        # STEP 1: Translate verilog to odb
        self._run_ord_cmd("floorplan.tcl", "2_1_floorplan.json", "2_1_floorplan.log")

        # STEP 2: IO Placement (random)
        self._run_ord_cmd(
            "io_placement_random.tcl", "2_2_floorplan_io.json", "2_2_floorplan_io.log"
        )

        # STEP 3: Timing Driven Mixed Sized Placement
        if "MACRO_PLACEMENT" not in os.environ:
            self._run_ord_cmd("tdms_place.tcl", "2_3_tdms.json", "2_3_tdms_place.log")
        else:
            print("Using manual macro placement file " + os.environ["MACRO_PLACEMENT"])
            shutil.copy(
                os.path.join(results_dir, "2_2_floorplan_io.odb"),
                os.path.join(results_dir, "2_3_floorplan_tdms.odb"),
            )

        # STEP 4: Macro Placement
        self._run_ord_cmd("macro_place.tcl", "2_4_mplace.json", "2_4_mplace.log")

        # STEP 5: Tapcell and Welltie insertion
        self._run_ord_cmd("tapcell.tcl", "2_5_tapcell.json", "2_5_tapcell.log")

        # STEP 6: PDN generation
        self._run_ord_cmd("pdn.tcl", "2_6_pdn.json", "2_6_pdn.log")

        shutil.copy(
            os.path.join(results_dir, "2_6_floorplan_pdn.odb"),
            os.path.join(results_dir, "2_floorplan.odb"),
        )

        print("floorplan done")

    # Place
    def placement(self, design: str = None, density: float = None):
        """Run placement.
        Placement can't be executed without performing floorplanning.
        Keyword parameters:
            design(str) -- Path the floorplaned lef file. If it's set to None, the floorplaned lef file will be read in the default path.
            density(float) -- The desired placement density of cells. It reflects how spread the cells would be on the core area. 1.0 = closely dense. 0.0 = widely spread.
        """

        if density is not None:
            os.environ["PLACE_DENSITY"] = str(density)
        results_dir = os.environ["RESULTS_DIR"]

        # STEP 1: Global placement without placed IOs, timing-driven, and routability-driven.
        status = self._run_ord_cmd(
            "global_place_skip_io.tcl",
            "3_1_place_gp_skip_io.json",
            "3_1_place_gp_skip_io.log",
        )
        if status != 0:
            return status

        # STEP 2: IO placement (non-random)
        status = self._run_ord_cmd(
            "io_placement.tcl", "3_2_place_iop.json", "3_2_place_iop.log"
        )
        if status != 0:
            return status

        # STEP 3: Global placement with placed IOs, timing-driven, and routability-driven.
        status = self._run_ord_cmd(
            "global_place.tcl", "3_3_place_gp.json", "3_3_place_gp.log"
        )
        if status != 0:
            return status

        # STEP 4: Resizing & Buffering
        status = self._run_ord_cmd("resize.tcl", "3_4_resizer.json", "3_4_resizer.log")
        if status != 0:
            return status

        # STEP 5: Detail placement
        status = self._run_ord_cmd(
            "detail_place.tcl", "3_5_opendp.json", "3_5_opendp.log"
        )

        shutil.copy(
            os.path.join(results_dir, "3_5_place_dp.odb"),
            os.path.join(results_dir, "3_place.odb"),
        )
        shutil.copy(
            os.path.join(results_dir, "2_floorplan.sdc"),
            os.path.join(results_dir, "3_place.sdc"),
        )

        print("placement done")

    # CTS
    def cts(self, design: str = None, tns_end_percent: int = 20):
        """Run clock tree synthesis.
        CTS can't be executed without performing placement.
        Keyword parameters:
            design(str) --  The path to the placed lef file. If it's set to None, the placed lef file will be read in the default path.
            tns_end_percent(float) -- Specifies how many percent of violating paths to fix [0-100]. Worst path will always be fixed
        """

        os.environ["TNS_END_PERCENT"] = str(tns_end_percent)
        self._run_ord_cmd("cts.tcl", "4_1_cts.json", "4_1_cts.log")
        self._run_ord_cmd(
            "fillcell.tcl", "4_2_cts_fillcell.json", "4_2_cts_fillcell.log"
        )
        results_dir = os.environ["RESULTS_DIR"]
        shutil.copy(
            os.path.join(results_dir, "4_2_cts_fillcell.odb"),
            os.path.join(results_dir, "4_cts.odb"),
        )

        print("cts done")

    # Route
    def global_route(self, design: str = None):
        """Run global routing.
        Global routing can't be executed without performing CTS.
        Keyword parameters:
            design(str) --  The path to the lef file with CTS. If it's set to None, the lef file with CTS will be read in the default path.
        """

        status = self._run_ord_cmd(
            "global_route.tcl", "5_1_fastroute.json", "5_1_fastroute.log"
        )
        
        print("global_route done")

    def detail_route(self, design: str = None):
        """Run detail routing.
        Detail routing can't be executed without performing global routing.
        Keyword parameters:
            design(str) --  The path to the global routed lef file. If it's set to None, the global routed lef file will be read in the default path.
        """

        self._run_ord_cmd(
            "detail_route.tcl", "5_2_TritonRoute.json", "5_2_TritonRoute.log"
        )
        results_dir = os.environ["RESULTS_DIR"]
        shutil.copy(
            os.path.join(results_dir, "5_2_route.odb"),
            os.path.join(results_dir, "5_route.odb"),
        )
        shutil.copy(
            os.path.join(results_dir, "4_cts.sdc"),
            os.path.join(results_dir, "5_route.sdc"),
        )

        print("detail_route done")

    # Finishing
    def density_fill(self):
        """Run density fill.
        Density fill can't be executed without performing routing.
        """

        if os.environ.get("DENSITY_FILL", "") != "":
            self._run_ord_cmd(
                "density_fill.tcl", "6_density_fill.json", "6_density_fill.log"
            )
        else:
            shutil.copy(
                os.path.join(os.environ["RESULTS_DIR"], "5_route.odb"),
                os.path.join(os.environ["RESULTS_DIR"], "6_1_fill.odb"),
            )

        print("density_fill done")

    # Finishing
    def final_report(self):
        """Run final report.
        Final report can't be executed without performing density fill.
        """

        self._run_ord_cmd("final_report.tcl", "6_report.json", "6_report.log")
        results_dir = os.environ["RESULTS_DIR"]
        shutil.copy(
            os.path.join(results_dir, "5_route.sdc"),
            os.path.join(results_dir, "6_1_fill.sdc"),
        )
        shutil.copy(
            os.path.join(results_dir, "5_route.sdc"),
            os.path.join(results_dir, "6_final.sdc"),
        )

        print("final_report done")

    def klayout(self):
        raise NotImplementedError

    def get_metric(self, stage: str, metrics: list):
        """Get metric of a stage.
        Get metric can't be executed before the provide stage has been executed.
        We can get PPA(ppa) metric by calculating power, performance and area metrics.
        Keyword parameters:
            stage(str) -- The stage to get the metric from.
            Available values are: "floorplan", "place", "cts", "route", "final".
            metrics(list(str)) -- The concerned metrics provided in a list.
            Available values are: "tns", "wns", "area", "power", "performance". 
        Return:
            metric(float) -- The value of metrics. The smaller the better.
        """

        # Note: the following implementation is generated by copilet
        # UNTESTED, but looks awesome
        stage_file = ""
        if stage == "floorplan":
            stage_file = "2_1_floorplan"
        elif stage == "final":
            stage = "finish"
            stage_file = "6_report"
        for metric in metrics:
            if metric == "tns":
                metric = stage + "__timing__setup__ts"
            elif metric == "wns":
                metric = stage + "__timing__setup__ws"
            elif metric == "area":
                metric = stage + "__design__core__area"
            elif metric == "power":
                metric = stage + "__power__total"
            elif metric == "performance":
                metric = stage + "__performance"

        m = 0
        with open(os.path.join(os.environ["LOG_DIR"], stage_file + ".json")) as f:
            data = json.load(f)
        for metric in metrics:
            m += data[metric]
        m /= len(metrics)

        print("get_metric done")
        return m

    def run_all(self):
        self._run_ord_cmd("run_all.tcl", "run_all.json", "run_all.log")

    def _run_ord_cmd(self, script: str, metric: str, log_to: str):
        cmd = " ".join(
            [
                self.time_cmd,
                self.ord_cmd,
                os.path.join(os.environ["SCRIPTS_DIR"], script),
                "-metrics",
                os.path.join(os.environ["LOG_DIR"], metric),
            ]
        )
        print(cmd)
        with open(os.path.join(os.environ["LOG_DIR"], log_to), "w") as log_file:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
            )
            self._print(result.stdout)
            log_file.write(result.stdout.decode())
        print("Done.", flush=True)
        return result.returncode


def tuned(func, param):
    """parameter tuning.
    Keyword parameters:
        func -- A function that runs the target flow and return a metric for parameter tuning.
        The function should take to-be-tuned parameters as its function parameters.
        The function should return the concerned results as its return value.
        param -- The flow parameters to be tuned.
        Param should be a dictionary with the following format:
        { param_name: {"minmax": [min, max], "step": step} }
        # The data type of min, max and step is required to be int or float
    """

    param_space = {}
    for name, para in param.items():
        param_space[name] = tune.quniform(
            para["minmax"][0], para["minmax"][1], para["step"]
        )
    searcher = OptunaSearch(metric=["area", "power"], mode=["min", "min"])
    algo = ConcurrencyLimiter(searcher, max_concurrent=1)

    tuner = tune.Tuner(
        tune.with_resources(func, resources={"cpu": 1, "gpu": 0}),
        tune_config=tune.TuneConfig(
            search_alg=algo, max_concurrent_trials=1, num_samples=20
        ),
        run_config=RunConfig(
            stop={"time_total_s": 600},  # 100 seconds
        ),
        param_space=param_space,
    )
    results = tuner.fit()
    print(
        "Best hyperparameters found for area were: ",
        results.get_best_result("area", "min").config,
    )
    print(
        "Best hyperparameters found for power were: ",
        results.get_best_result("power", "min").config,
    )
    print("tune done")


if __name__ == "__main__":
    # ceda = chateda()
    # ceda.setup(
    #     "aes",
    #     "nangate45",
    #     verilog="./flow/designs/src/aes/aes_cipher_top.v",
    #     flow_home="./flow",
    # )
    # ceda.run_synthesis(abc_area=True)
    # ceda.floorplan(core_utilization=50, macro_place_halo=3, macro_place_channel=8)
    # ceda.placement(density=0.6)
    # ceda.cts()  # tns_end_percent=100)
    # ceda.global_route()
    # ceda.detail_route()
    # ceda.density_fill()
    # ceda.final_report()
    # exit(0)

    def tune_synth(config):
        ceda = chateda()
        ceda.setup(
            "jpeg",
            "nangate45",
            # verilog="./flow/designs/src/aes/aes_cipher_top.v",
            flow_home="./flow",
        )
        # ceda.run_synthesis(abc_area=True)
        ceda.floorplan(
            core_utilization=config["util"],
            core_aspect_ratio=config["ratio"],
            core_margins=config["margins"],
            macro_place_halo=config["halo"],
            macro_place_channel=config["channel"],
        )
        status = ceda.placement(density=config["density"])
        if status != 0:
            session.report({"area": 9999999, "power": 9999999, "wns": -9999999})
            return
        ceda.cts(tns_end_percent=config["tns_p"])
        # ceda.cts()
        status = ceda.global_route()
        if status != 0:
            session.report({"area": 9999999, "power": 9999999, "wns": -9999999})
            return
        ceda.detail_route()
        ceda.density_fill()
        print("\n\n\n before final report\n\n\n")
        ceda.final_report()
        print("\n\n\n after final report\n\n\n", flush=True)
        area = ceda.get_metric("final", "area")
        power = ceda.get_metric("final", "power")
        wns = ceda.get_metric("final", "wns")
        session.report({"area": area, "power": power, "wns": wns})

    tuned(
        tune_synth,
        {
            "util": {"minmax": [60, 90], "step": 10},
            "ratio": {"minmax": [0.8, 1.2], "step": 0.1},
            "margins": {"minmax": [8, 12], "step": 1},
            "halo": {"minmax": [5, 9], "step": 1},
            "channel": {"minmax": [7, 11], "step": 1},
            "density": {"minmax": [0.6, 0.9], "step": 0.1},
            "tns_p": {"minmax": [30, 50], "step": 5},
        },
    )