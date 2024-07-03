"""Constraint programming for employee scheduling."""


from ortools.sat.python import cp_model


model = cp_model.CpModel()

# The employees and the roles they are qualified for
employees = {"Phil": ["Restocker"],
             "Emma": ["Cashier", "Restocker"],
             "David": ["Cashier", "Restocker"],
             "Rebecca": ["Cashier"]}

# List of days for the schedule
days = ["Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"]

# List of shifts in a day
shifts = ["Morning",
          "Afternoon",
          "Evening"]

# List of possible roles
roles = ["Cashier",
         "Restocker"]

# `schedule[e][r][d][s]` indicates if employee `e`
# works role `r` on day `d` during shift `s`
schedule = {e:
            {r:
             {d:
              {s: model.new_bool_var(f"schedule_{e}_{r}_{d}_{s}")
               for s in shifts}
              for d in days}
             for r in roles}
            for e in employees}

# A cashier has to be present at all times
for d in days:
    for s in shifts:
        model.add(sum(schedule[e]["Cashier"][d][s]
                      for e in employees)
                  == 1)

# We need a restocker once per day
for d in days:
    model.add(sum(schedule[e]["Restocker"][d][s]
                  for e in employees
                  for s in shifts)
              == 1)

# Two restocking shifts should not be adjacent
for i in range(len(days)-1):
    model.add(sum(schedule[e]["Restocker"][days[i]]["Evening"] +
                  schedule[e]["Restocker"][days[i+1]]["Morning"]
                  for e in employees)
              <= 1)

# An employee can only work one role per shift
for e in employees:
    for d in days:
        for s in shifts:
            model.add(sum(schedule[e][r][d][s]
                          for r in roles)
                      <= 1)

# An employee can only be assigned 8 hours of work
# per day (with no idle time in-between shifts)
for e in employees:
    for d in days:
        model.add(sum(schedule[e][r][d]["Morning"] +
                      schedule[e][r][d]["Evening"]
                      for r in roles)
                  <= 1)

# Some employees are not qualified for certain roles
for e in employees:
    for r in roles:
        for d in days:
            for s in shifts:
                if r not in employees[e]:
                    model.add(schedule[e][r][d][s] == 0)

# Do not assign more than 10 shifts to the same employee in the same week
for e in employees:
    model.add(sum(schedule[e][r][d][s]
                  for r in roles
                  for d in days
                  for s in shifts)
              <= 10)

# Phil must work 4 shifts per week
model.add(sum(schedule["Phil"][r][d][s]
              for r in roles
              for d in days
              for s in shifts)
          == 4)

# Phil cannot work during the day from Monday to Friday
model.add(sum(schedule["Phil"][r][d][s]
              for r in roles
              for d in days if d not in ["Saturday", "Sunday"]
              for s in shifts if s in ["Morning", "Afternoon"])
          == 0)

# Don't assign Phil and Emma to the same shifts
for d in days:
    for s in shifts:
        model.add(sum(schedule[e][r][d][s]
                      for e in ["Phil", "Emma"]
                      for r in roles)
                  <= 1)

# Assign the weekend shifts equally between all employees
for e in employees:
    model.add(sum(schedule[e][r][d][s]
                  for r in roles
                  for d in ["Saturday", "Sunday"]
                  for s in shifts)
              == 2)

# Emma doesn't work from Monday to Wednesday
model.add(sum(schedule["Emma"][r][d][s]
              for r in roles
              for d in ["Monday", "Tuesday", "Wednesday"]
              for s in shifts)
          == 0)

# `total_shifts[e]` indicates the number of shifts assigned to employee `e`
total_shifts = {e: model.new_int_var(0, 10, f"total_shifts_{e}")
                for e in employees}

# Link `total_shifts` and `schedule`
for e in employees:
    model.add(total_shifts[e] == sum(schedule[e][r][d][s]
                                     for r in roles
                                     for d in days
                                     for s in shifts))

# `min_shifts` and `max_shifts` indicate the minimum and
# maximum number of shifts assigned to any employee
min_shifts = model.new_int_var(0, 10, "min_shifts")
max_shifts = model.new_int_var(0, 10, "max_shifts")

# Link `min_shifts`/`max_shifts` and `total_shifts`
model.add_min_equality(min_shifts, [total_shifts[e] for e in employees if e != "Phil"])
model.add_max_equality(max_shifts, [total_shifts[e] for e in employees if e != "Phil"])

# Objective: Distribute the shifts fairly between employees
model.minimize(max_shifts - min_shifts)

# Solve the model
solver = cp_model.CpSolver()
solver.solve(model)

# Print the solution
print(f"{' '*10} | " +
      " | ".join([f"{d:^9}" for d in days]) +
      " | Total |")

print(f"{' '*10} | " +
      ' | '.join([f"M | A | E" for d in range(len(days))]) +
      " |       |")

for e in employees:
    shifts_worked = sum([solver.value(schedule[e][r][d][s])
                         for r in roles
                         for s in shifts
                         for d in days])

    print(f"{e:<10} | " +
          ' | '.join(["C" if solver.value(schedule[e]["Cashier"][d][s]) == 1 else
                      "R" if solver.value(schedule[e]["Restocker"][d][s]) == 1 else " "
                      for d in days
                      for s in shifts]) +
          " | " +
          f"{shifts_worked:^5}" +
          " | ")
