class chateda:
    def __init__(self) -> None:
        """User Guide: Any steps in follows can't be executed unless the previous step has been executed. The usual flow of chip designing goes like this in sequence: a. Setup; b. Synthesis; c. Floorplanning; d. Placement; e. Clock Tree Synthesis (CTS); f. Global Routing; g. Detailed Routing; h. Density Fill; i. Final Report; 
        """
        # init chateda class
        print("init done")

    # Setup
    def setup(
        self,
        design_name: str,
        platform: str,
        flow_home: str = ".",
        verilog: str = None,
        sdc: str = None,
    ):
        """Setup EDA tool.
        Keyword parameters:
            design_name(str) -- The name of the top-level module of the design.
            platform(str) -- Specifies process design kit or technology node to be used. Supported options are "asap7", "nangate45", "sky130", and "gf180".
            flow_home(str) -- The path to the flow home directory.
            verilog(str) -- The path to the design Verilog files.
            sdc(str) --  The path to design constraint (SDC) file.
        """
        # setting up EDA tool
        print("setup done")

    # Synthesis
    def run_synthesis(self, clock_period: int = None, abc_area: bool = False):
        """Run logic synthesis.
        Logic synthesis can't be executed without setting up.
        Keyword parameters:
            clock_period(int) -- Clock period to be used by STA during synthesis. Default value read from constraint.sdc
            abc_area(bool) -- Strategies for Yosys ABC synthesis: Area/Speed. Default ABC_SPEED.
        """
        # running logic synthesis
        # generating the gate netlist file in the default path.
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
        # running floorplan
        # generating the floorplaned lef file in the default path.
        print("floorplan done")

    # Place
    def placement(self, design: str = None, density: float = None):
        """Run placement.
        Placement can't be executed without performing floorplanning.
        Keyword parameters:
            design(str) -- Path the floorplaned lef file. If it's set to None, the floorplaned lef file will be read in the default path.
            density(float) -- The desired placement density of cells. It reflects how spread the cells would be on the core area. 1.0 = closely dense. 0.0 = widely spread.
        """
        # running placement
        # generating the placed lef file in the default path.
        print("placement done")

    # CTS
    def cts(self, design: str = None, tns_end_percent: int = 20):
        """Run clock tree synthesis.
        CTS can't be executed without performing placement.
        Keyword parameters:
            design(str) --  The path to the placed lef file. If it's set to None, the placed lef file will be read in the default path.
            tns_end_percent(float) -- Specifies how many percent of violating paths to fix [0-100]. Worst path will always be fixed
        """
        # running clock tree synthesis
        # generating the lef file with CTS in the default path.
        print("cts done")

    # Route
    def global_route(self, design: str = None):
        """Run global routing.
        Global routing can't be executed without performing CTS.
        Keyword parameters:
            design(str) --  The path to the lef file with CTS. If it's set to None, the lef file with CTS will be read in the default path.
        """
        # performing global routing
        # generating the global routed lef file in the default path.
        print("global_route done")

    def detail_route(self, design: str = None):
        """Run detail routing.
        Detail routing can't be executed without performing global routing.
        Keyword parameters:
            design(str) --  The path to the global routed lef file. If it's set to None, the global routed lef file will be read in the default path.
        """
        # performing detail routing
        print("detail_route done")

    # Finishing
    def density_fill(self):
        """Run density fill.
        Density fill can't be executed without performing routing.
        """
        # performing density fill
        print("density_fill done")

    # Finishing
    def final_report(self):
        """Run final report.
        Final report can't be executed without performing density fill.
        """
        # generating the final report
        print("final_report done")

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
            metric(float) -- The performance value of metrics. The smaller the better.
        """
        metric = 0
        # metric(s) calculation
        print("get_metric done")
        return metric

def tune(func, param):
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
    # peforming dse(parameter tuning) for chateda
    print("tune done")