import streamlit as st
import pandas as pd
import random
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Class Group Generator (4 Classes)", layout="wide")

st.title("🧑‍🏫 Class Group Generator – 4 Classes")

st.markdown("""
Upload a CSV with:
- `Name`, `Gender`, `SEN`, `Attainment`
- `Friend1`–`Friend5`: five chosen friends
- `Avoid1`–`Avoid3`: pupils to avoid
""")

uploaded = st.file_uploader("📤 Upload your CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded).fillna("")
    st.success("File uploaded!")

    students = df["Name"].tolist()
    max_class_size = 18
    classes = [[] for _ in range(4)]

    friend_map = {
        row["Name"]: [row[f"Friend{i}"] for i in range(1, 6) if row[f"Friend{i}"]]
        for _, row in df.iterrows()
    }
    avoid_map = {
        row["Name"]: [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]]
        for _, row in df.iterrows()
    }
    student_info = df.set_index("Name")[["Gender", "SEN"]].to_dict("index")

    name_to_class = {}
    placed = set()
    unplaced = []

    def can_place(student, group):
        if len(group) >= max_class_size:
            return False
        for peer in group:
            if peer in avoid_map[student] or student in avoid_map.get(peer, []):
                return False
        return True

    random.shuffle(students)

    for student in students:
        if student in placed:
            continue

        friends = friend_map.get(student, [])
        friend_in_class = False

        for friend in friends:
            if friend in name_to_class:
                friend_class = name_to_class[friend]
                if can_place(student, classes[friend_class]):
                    classes[friend_class].append(student)
                    name_to_class[student] = friend_class
                    placed.add(student)
                    friend_in_class = True
                    break

        if friend_in_class:
            continue

        for friend in friends:
            if friend not in placed:
                for group_id in sorted(range(len(classes)), key=lambda x: len(classes[x])):
                    group = classes[group_id]
                    if can_place(student, group) and can_place(friend, group):
                        group.extend([student, friend])
                        name_to_class[student] = group_id
                        name_to_class[friend] = group_id
                        placed.add(student)
                        placed.add(friend)
                        friend_in_class = True
                        break
                if friend_in_class:
                    break

        if not friend_in_class:
            for group_id in sorted(range(len(classes)), key=lambda x: len(classes[x])):
                if can_place(student, classes[group_id]):
                    classes[group_id].append(student)
                    name_to_class[student] = group_id
                    placed.add(student)
                    friend_in_class = True
                    break

        if not friend_in_class:
            unplaced.append(student)

    st.header("📋 Class Lists")
    results = []
    transposed = {f"Class {i+1}": group for i, group in enumerate(classes)}
    transposed["Unplaced"] = unplaced

    max_rows = max(len(v) for v in transposed.values())
    export_data = {
        key: v + [""] * (max_rows - len(v)) for key, v in transposed.items()
    }
    export_df = pd.DataFrame(export_data)
    st.dataframe(export_df)

    st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False)
    excel_buffer.seek(0)
    st.download_button("📥 Download Excel", data=excel_buffer, file_name="assignments.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    for i, group in enumerate(classes):
        st.subheader(f"Class {i+1} – Visual Breakdown")

        genders = [student_info[n]["Gender"] for n in group if n in student_info]
        plt.figure(figsize=(1.5, 1.5))
        plt.pie([genders.count("M"), genders.count("F")], labels=["M", "F"], autopct="%1.1f%%")
        plt.title("Gender")
        st.pyplot(plt.gcf())
        plt.clf()

        sens = [student_info[n]["SEN"] for n in group if n in student_info]
        plt.figure(figsize=(1.5, 1.5))
        plt.pie([sens.count("Yes"), sens.count("No")], labels=["SEN", "No SEN"], autopct="%1.1f%%")
        plt.title("SEN")
        st.pyplot(plt.gcf())
        plt.clf()

    st.subheader("🔍 Friendship Placement Summary")
    # Visualisation will now appear before pie charts
    visual_data = []
    for _, row in df.iterrows():
        name = row["Name"]
        row_class = name_to_class.get(name, "Unplaced")
        summary = {"Name": name, "Class": row_class}
        class_group = classes[row_class] if isinstance(row_class, int) else []

        for i in range(1, 6):
            f = row[f"Friend{i}"]
            if not f:
                summary[f"Friend{i}"] = ""
            elif f in class_group:
                summary[f"Friend{i}"] = f"✅ {f}"
            else:
                summary[f"Friend{i}"] = f"❌ {f}"
        visual_data.append(summary)

    vis_df = pd.DataFrame(visual_data)
    st.dataframe(vis_df)
