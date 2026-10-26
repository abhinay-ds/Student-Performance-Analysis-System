"""
Page 5: Educational Study Materials Repository.
Students browse and download lecture notes, slides, and syllabus documents for their course/semester.
Professors upload, categorize, and publish academic resources.
"""

from pathlib import Path
import streamlit as st
import database
import auth
import permissions
import academic_service
import ui_theme
from config import COURSES, SEMESTERS, ALLOWED_MATERIAL_EXTENSIONS, MAX_UPLOAD_FILE_SIZE_MB

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

# ============================================================================
# STUDENT STUDY MATERIALS VIEW
# ============================================================================
if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked.")
        st.stop()

    materials_df = database.get_study_materials(course=student["course"], semester=student["semester"])

    ui_theme.render_header(
        title="Study Materials & Resources",
        subtitle=f"Lecture notes, reference slides, and revision materials for {student['course']} (Semester {student['semester']})",
        badge_text=f"{len(materials_df)} Resources" if not materials_df.empty else "No Documents",
        badge_variant="info",
    )

    if materials_df.empty:
        st.info(f"No study materials currently published for {student['course']} (Semester {student['semester']}).")
    else:
        for _, mat in materials_df.iterrows():
            fpath = Path(mat["file_path"])
            ext_label = fpath.suffix.upper().replace(".", "") if fpath.suffix else "DOC"
            st.markdown(
                f"""
                <div class="saas-card">
                    <div class="saas-card-header">
                        <span class="saas-card-title">{mat['title']}</span>
                        {ui_theme.render_badge(mat['subject_name'], 'primary')}
                    </div>
                    <p style="color: #475569; font-size: 14px; margin: 0 0 12px 0;">{mat['description']}</p>
                    <small style="color: #94A3B8;">Published on {mat['uploaded_at'][:10]}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if fpath.exists():
                with open(fpath, "rb") as f:
                    st.download_button(
                        f"Download Document ({ext_label})",
                        data=f.read(),
                        file_name=fpath.name,
                        key=f"dl_mat_{mat['id']}",
                    )
            else:
                st.caption("File resource currently unavailable on disk.")
            st.write("")

# ============================================================================
# PROFESSOR STUDY MATERIALS UPLOAD & MANAGEMENT VIEW
# ============================================================================
else:
    auth_subjects = permissions.get_professor_authorized_subjects()

    ui_theme.render_header(
        title="Study Materials Management",
        subtitle="Upload lecture slides, syllabus sheets, and curriculum resources for enrolled cohorts",
        badge_text="Faculty Operations",
        badge_variant="primary",
    )

    tab_upload, tab_view = st.tabs(["Upload Resource", "Published Materials Directory"])

    with tab_upload:
        st.subheader("Upload Academic Resource")
        with st.form("upload_material_form"):
            c1, c2 = st.columns(2)
            with c1:
                m_title = st.text_input("Resource Title *", placeholder="e.g. Unit 2 Memory Management & Paging")
                m_subject = st.selectbox("Subject *", auth_subjects)
                m_course = st.selectbox("Target Course *", COURSES)
            with c2:
                m_sem = st.selectbox("Target Semester *", SEMESTERS)
                m_desc = st.text_area("Description / Topic Summary *", placeholder="Key topics covered in this document...")

            m_file = st.file_uploader(
                f"Select Document File (Allowed: {', '.join(ALLOWED_MATERIAL_EXTENSIONS)}, Max: {MAX_UPLOAD_FILE_SIZE_MB}MB) *",
                type=[ext.replace(".", "") for ext in ALLOWED_MATERIAL_EXTENSIONS],
            )

            submit_mat = st.form_submit_button("Upload and Publish Resource", type="primary", use_container_width=True)

            if submit_mat:
                if permissions.prevent_demo_mutation():
                    pass
                elif not m_title or not m_subject or not m_desc or not m_file:
                    st.error("All fields and an uploaded file are required.")
                elif m_file.size > MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024:
                    st.error(f"File exceeds maximum permitted size of {MAX_UPLOAD_FILE_SIZE_MB}MB.")
                else:
                    curr_user = permissions.get_current_user() or {}
                    academic_service.upload_study_resource(
                        title=m_title,
                        subject_name=m_subject,
                        course=m_course,
                        semester=m_sem,
                        uploaded_file=m_file,
                        description=m_desc,
                        uploaded_by=curr_user.get("id"),
                    )
                    st.success(f"Resource '{m_title}' uploaded and published successfully!")
                    st.rerun()

    with tab_view:
        st.subheader("Published Educational Resources")
        all_materials = database.get_study_materials()
        if all_materials.empty:
            st.info("No study materials uploaded yet.")
        else:
            st.dataframe(
                all_materials[["id", "title", "subject_name", "course", "semester", "uploaded_at"]].rename(
                    columns={
                        "id": "ID",
                        "title": "Title",
                        "subject_name": "Subject",
                        "course": "Course",
                        "semester": "Sem",
                        "uploaded_at": "Uploaded On",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

