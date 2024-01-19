import json
import requests
import re
import datetime
from random import randint

class SetEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set):
      return list(obj)
    return json.JSONEncoder.default(self, obj)


COURSES = [
  {
    'subject': 'MATH',
    'code': '100'
  },
  {
    'subject': 'CSC',
    'code': '111'
  },
  {
    'subject': 'MATH',
    'code': '110',
  },
  {
    'subject': 'PHYS',
    'code': '110'
  },
  {
    'subject': 'ENGR',
    'code': '110',
  },
  {
    'subject': 'ENGR',
    'code': '130',
  }
]

# groups:
# 1 = start hour
# 2 = start minute
# 3 = start am or pm
# 4 = end hour
# 5 = end minute
# 6 = end am or pm
time_extractor = re.compile(r'(\d{1,2}):(\d{2})\s([a|p]m)\s-\s(\d{1,2}):(\d{2})\s([a|p]m)')


# {
#   meeting_times: [
#     {
#       days: "MWR",
#       start_time: {
#         hr: 12,
#         mi: 00,
#       },
#       end_time: {
#         hr: 13,
#         mi: 20,
#       },
#     },
#     {
#       days: "T",
#       start_time: {
#         hr: 16,
#         mi: 00,
#       },
#       end_time: {
#         hr: 17,
#         mi: 50,
#       },
#     }
#   ],
#   meeting_times_hash: "abcdef",
#   section_type: "A, B, T",
#   crn: "123456",
# }

def to_24_hour(hour, suffix):
  if suffix == "pm" and hour < 12:
    return hour + 12
  
  return hour


def is_before(first, second):
  if first["hr"] < second["hr"]:
    return True
  
  if first["hr"] == second["hr"] and first["mi"] < second["mi"]:
    return True
  
  return False


def is_after(first, second): 
  if first["hr"] > second["hr"]:
    return True
  
  if first["hr"] == second["hr"] and first["mi"] > second["mi"]:
    return True
  
  return False


def meeting_times_conflict(one, two):
  # if end time of meeting one is after the start time of meeting two on the same day
  # or if the end time of meeting two is after the start time of meeting one on the same day 
  if len(one["days"].intersection(two["days"])) > 0:
    # print("both meetings occur on the same day")
    # print(f"one: {one}")
    # print(f"two: {two}")

    # 14:30 >= 9:20 and 8:30 >= 15:20
    return not is_before(one["end_time"], two["start_time"]) and not is_after(one["start_time"], two["end_time"])

  return False

def has_conflict(meeting_times: list, earliest_start_hour: int, latest_end_hour: int):
  for meeting in meeting_times:
    if meeting["start_time"]["hr"] < earliest_start_hour:
      return True

    if meeting["end_time"]["hr"] >= latest_end_hour:
      return True

  for i, time in enumerate(meeting_times):
    for j in range(len(meeting_times)):
      if i != j:
        if meeting_times_conflict(meeting_times[i], meeting_times[j]):
          # print(f"meeting times conflict: {meeting_times[i]}, {meeting_times[j]}")
          return True

  return False


def process_section(section: dict) -> dict:
  # print(section)
  result = {
    "meeting_times": [],
    "section_type": section["sectionCode"][0],
    "crn": section["crn"],
  }

  for meeting in section["meetingTimes"]:
    # print(meeting["time"])
    if meeting["time"] != "TBA": 
      m = time_extractor.match(meeting["time"])

      meeting_info = {
        "days": set(meeting["days"]),
        "start_time": {
          "hr": to_24_hour(int(m.group(1)), m.group(3)),
          "mi": int(m.group(2)),
        },
        "end_time": {
          "hr": to_24_hour(int(m.group(4)), m.group(6)),
          "mi": int(m.group(5)),
        }
      }

      result["meeting_times"].append(meeting_info)

  # print(type(result["meeting_times"]))
  # fs = frozenset(result["meeting_times"])  
  # result["meeting_times_hash"] = hash(fs)

  return result


{
  "meeting_times": {},
  "crns": [],
  "type": "A|B|T",
}

def process_courses(course_list):
  processed_courses = []

  for course in course_list:
    # print(course["subject"])
    # print(course["code"])
    sections = {
      'A': [],
      'B': [],
      'T': [],
    }
    url = f"https://courseup.vikelabs.ca/api/sections/202309?subject={course['subject']}&code={course['code']}&v9=true"
    course_name = f"{course['subject']}{course['code']}"
    # print(url)
    res = requests.get(url)
    if res.status_code == 200:
      for section in res.json():
        s = process_section(section)

        found_same = False
        for sec in sections[s["section_type"]]:
          if sec["meeting_times"] == s["meeting_times"]:
            sec["crns"].append(s["crn"])
            sec["codes"].append(section["sectionCode"])
            found_same = True
            # print("found duplicate:")
            # print(s)

        if not found_same:
          sections[s["section_type"]].append({
            "crns": [s["crn"]],
            "meeting_times": s["meeting_times"],
            "type": s["section_type"],
            "name": course_name,
            "codes": [section["sectionCode"]]
          })

    processed_courses.append({
      "name": course_name,
      "sections": sections,
    })


  num_permutations = 1
  # print("starting output:")
  for course in processed_courses:
    # print(course["name"])
    for section_type in course["sections"].keys():
      num_unique = len(course['sections'][section_type])
      if num_unique > 0:
        num_permutations *= num_unique
        print(f"course name: {course['name']}, section type: {section_type}, # of unique sections: {len(course['sections'][section_type])}")
      # print(json.dumps(course["sections"][section_type], indent=2))
      pass
  
  # print(json.dumps(processed_courses, indent=2))
  print(f"number of permutations: {num_permutations}")

  return num_permutations, processed_courses
      

def main():
  perms, courses = process_courses(COURSES)
  # print(json.dumps(courses, indent=2, cls=SetEncoder))
  
  # N = 1000000
  N = 110702592

  delta_ms = 0
  found_non_conflicted = False
  non_conflicting = []

  desired_sections = []

  meetings_to_check = []

  for course in courses:
    for section_type in course["sections"]:
      sections = course["sections"][section_type]
      if len(sections) > 0:
        desired_sections.append(sections)
        # # print(sections[0])
        # idx = randint(0, len(sections) - 1)

        # for meeting in sections[idx]["meeting_times"]:
        #   meetings_to_check.append(meeting)


    # print(meetings_to_check)

    # start = datetime.datetime.now()
    # conflicted = has_conflict(meetings_to_check)
    # end = datetime.datetime.now()
    # delta_ms += (end - start).total_seconds() * 1000
    # if not conflicted:
    #   non_conflicting.append(meetings_to_check)
    
    # if i % 1000000 == 0 and i > 0:
    #   print(f"checked {i} so far, found non-conflicting schedule? {found_non_conflicted}, average time = {delta_ms / i} milliseconds")

  
  print(len(desired_sections))
  indexes = [0] * len(desired_sections)
  start_time = datetime.datetime.now()

  try:
    for count in range(perms):
      # print(indexes)
      meetings_to_check = []
      current_sections = []
      for i in range(len(indexes)):
        section = desired_sections[i][indexes[i]]
        for meeting in section["meeting_times"]:
          meetings_to_check.append(meeting)
        current_sections.append(section)
      
      conflicted = has_conflict(meetings_to_check, 7, 17)
      if not conflicted:
        non_conflicting.append(current_sections)

      indexes[-1] += 1
      for i in range(len(indexes) - 1, 0, -1):
        # print(len(desired_sections[i]))
        if indexes[i] == len(desired_sections[i]):
          indexes[i] = 0
          indexes[i - 1] += 1  
      
      if count % 1000000 == 0 and count > 0:
        print(f"checked {count} so far, non-conflicting length: {len(non_conflicting)}")
  except KeyboardInterrupt:
    pass

  
  end_time = datetime.datetime.now()
  print(f"found non-conflicting schedule? {len(non_conflicting)}")
  print(f"elapsed time: {(end_time - start_time).total_seconds()} seconds")
  # print(json.dumps(non_conflicting[-1], indent=2, cls=SetEncoder))
  for schedule in non_conflicting:
    print("==== START SCHEDULE")
    for section in schedule:
      print(f"{section['name']}: {section['codes']}")

  print(len(non_conflicting))

if __name__ == "__main__":
  main()