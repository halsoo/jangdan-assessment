"""
리듬꼴 정간보에서 각 음표의 온셋 시간을 계산하는 스크립트.

- 각 장단 안의 템포는 일정하다고 가정 (선형 보간)
- 장단 i의 끝 시간 = 장단 i+1의 시작 시간
- 마지막 장단은 직전 장단의 박 길이를 이용해 끝 시간 추정
- 쉬는 박 (공백 or 빈 칸)은 결과에서 제외
"""

import csv

INPUT_FILE = "jangdan_start.csv"
OUTPUT_FILE = "note_onsets.csv"


def expand_cell_notes(cell: str):
    note = cell.strip()
    if not note:
        return []

    if note == "덕더":
        return [("덕", 0.0, 0.75), ("더", 0.75, 0.25)]

    if note == "덕덕":
        return [("덕", 0.0, 0.5), ("덕", 0.5, 0.5)]

    return [(note, 0.0, 1.0)]


def parse_onsets(input_file: str, output_file: str) -> None:
    # CSV 읽기
    rows = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # TIME, LABEL, 리듬꼴, 총박수
        for row in reader:
            if any(row):  # 빈 행 제외
                rows.append(row)

    results = []

    for i, row in enumerate(rows):
        time = float(row[0])
        label = row[1]
        rhythm = row[2]
        total_beats = int(row[3])

        # 장단 끝 시간 계산
        if i < len(rows) - 1:
            end_time = float(rows[i + 1][0])
        else:
            # 마지막 행: 직전 장단의 박 길이로 추정
            prev_time = float(rows[i - 1][0])
            beat_dur = (time - prev_time) / int(rows[i - 1][3])
            end_time = time + beat_dur * total_beats

        beat_duration = (end_time - time) / total_beats

        # 리듬꼴 파싱: | 구분으로 각 정간(박) 분리
        cells = rhythm.split("|")

        for beat_idx, cell in enumerate(cells):
            expanded_notes = expand_cell_notes(cell)
            if not expanded_notes:  # 쉬는 박 제외
                continue

            for note, offset_ratio, duration_ratio in expanded_notes:
                onset_time = time + (beat_idx + offset_ratio) * beat_duration

                results.append(
                    {
                        "onset_time": round(onset_time, 6),
                        "label": label,
                        "beat_index": beat_idx,
                        "note": note,
                        "jangdan_start": round(time, 9),
                        "beat_duration": round(beat_duration, 6),
                    }
                )

    # 결과 저장
    fieldnames = ["onset_time", "label", "beat_index", "note", "jangdan_start", "beat_duration"]
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"저장 완료: {output_file}  ({len(results)}개 음표)")


if __name__ == "__main__":
    parse_onsets(INPUT_FILE, OUTPUT_FILE)
