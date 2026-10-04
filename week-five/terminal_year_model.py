"""Stylized replication of DICE-2023's cost-benefit-optimal policy vs its baseline.
Every input is a published DICE-2023 number (Barrage & Nordhaus, NBER WP 31112, April 2023)
except the assumptions flagged ASSUMED."""
import math

def interp(points, x):
    pts = sorted(points)
    if x <= pts[0][0]: return pts[0][1]
    if x >= pts[-1][0]: return pts[-1][1]
    for (x0,y0),(x1,y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1-y0)*(x-x0)/(x1-x0)

# --- published anchors (NBER WP 31112, Tables 3 and 4) ---
T_CB   = [(2020,1.25),(2025,1.43),(2050,1.95),(2100,2.73),(2150,2.78)]
T_BASE = [(2020,1.25),(2025,1.43),(2050,2.15),(2100,3.80),(2150,5.42)]
MU_CB   = [(2020,.05),(2030,.24),(2040,.32),(2050,.40),(2060,.46),(2100,.76)]
MU_BASE = [(2020,.05),(2030,.06),(2040,.07),(2050,.07),(2060,.08),(2100,.10)]
PSI2 = 0.003467            # damage = PSI2 * T^2
THETA1_0, THETA2 = 0.109062, 2.6
THETA1_2100 = 0.027        # zero-emission abatement cost is 2.7% of output in 2100
D_DECLINE = math.log(THETA1_0/THETA1_2100)/80    # ~1.7%/yr, as stated in the paper
Y2015, Y2100 = 118.3, 774.1                       # world output, trillions 2019$ (Table 8, baseline)
G_TO_2100 = math.log(Y2100/Y2015)/85
G_AFTER_2100 = 0.01        # ASSUMED output growth after 2100

def output(t):
    if t <= 2100: return Y2015*math.exp(G_TO_2100*(t-2015))
    return Y2100*math.exp(G_AFTER_2100*(t-2100))

def theta1(t): return THETA1_0*math.exp(-D_DECLINE*(min(t,2100)-2020))   # ASSUMED flat after 2100

def avoided_damage_share(t):
    tb, tc = interp(T_BASE,t), interp(T_CB,t)                              # ASSUMED flat after 2150
    return PSI2*(tb**2 - tc**2)

def abatement_cost_share(t):
    return theta1(t)*(interp(MU_CB,t)**THETA2 - interp(MU_BASE,t)**THETA2) # ASSUMED mu flat after 2100

def net_share(t): return avoided_damage_share(t) - abatement_cost_share(t)

def disc_path(kind):
    """annual goods discount rate by year; DICE: 4.5% in 2020 falling to 3.4% in 2100 (ASSUMED linear, flat after)."""
    def r(t):
        if kind == "dice": return 0.045 + (0.034-0.045)*min(max(t-2020,0),80)/80
        return kind
    return r

def cumulative(kind, start=2021, end=2300):
    r = disc_path(kind); df = 1.0; cum = 0.0; out = {}
    for t in range(start, end+1):
        df /= (1+r(t))
        cum += net_share(t)*output(t)*df
        out[t] = cum
    return out

def cumulative_parts(kind, start=2021, end=2300):
    """Running present value of costs and of avoided damage, kept separate (trillions of 2019 dollars)."""
    r = disc_path(kind); df = 1.0; ben = cost = 0.0; out = {}
    for t in range(start, end+1):
        df /= (1+r(t))
        ben  += avoided_damage_share(t)*output(t)*df
        cost += abatement_cost_share(t)*output(t)*df
        out[t] = (ben, cost)
    return out

if __name__ == "__main__":
    print("D_DECLINE per yr:", round(D_DECLINE,5), "| g to 2100:", round(G_TO_2100,4), "| Y2020:", round(output(2020),1))
    print("Check damage fn vs paper: base 2100 %.2f%% (paper 5.0), CB 2100 %.2f%% (paper 2.6)" %
          (100*PSI2*3.80**2, 100*PSI2*2.73**2))
    print("\nyear  avoided%  cost%   net%   outputT")
    for t in (2030,2050,2075,2100,2150,2200,2300):
        print(t, " %.3f  %.3f  %.3f  %.0f" % (100*avoided_damage_share(t),100*abatement_cost_share(t),100*net_share(t),output(t)))
    ends = (2050,2075,2100,2150,2200,2300)
    for kind in ("dice", 0.02, 0.01, 0.05):
        c = cumulative(kind, end=2520)
        print("\nrate", kind, " cumulative net PV (trillions 2019$) to:", {e: round(c[e],1) for e in ends}, "| to 2520:", round(c[2520],1))
        tot=c[2300]; print("   share of 2300 total by 2050/2100/2200:", [round(c[e]/tot,3) for e in (2050,2100,2200)])
    # first year net turns positive, and year cumulative net PV turns positive (DICE path)
    c = cumulative("dice", end=2300)
    print("\nfirst year net share > 0:", next(t for t in range(2021,2301) if net_share(t)>0))
    print("first year cumulative PV > 0 (DICE rate):", next((t for t in range(2021,2301) if c[t]>0), None))
    for rate in (0.02,0.01):
        cc = cumulative(rate, end=2300); print("first year cumulative PV > 0 at", rate, ":", next((t for t in range(2021,2301) if cc[t]>0), None))
