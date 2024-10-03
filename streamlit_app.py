import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
from st_flexible_callout_elements import flexible_callout

# Image URL
image_url = 'http://www.snuh.org/upload/about/hi/15e707df55274846b596e0d9095d2b0e.png'
st.image(image_url, use_column_width=False)

# Title
st.markdown("<h1 class='title'>🎈 Reading Encoder System for SNUHGCHC</h1>", unsafe_allow_html=True)

# Contact Info
st.markdown(
    """<div style='text-align: right; font-size: 12px; color: grey;'>오류 문의: 헬스케어연구소 김희연 (hui135@snu.ac.kr)</div>""",
    unsafe_allow_html=True,
)

st.divider()

# Password for accessing the site
PASSWORD = "snuhgchc"  # Change this to your desired password

# Password input from user
def login():
    st.sidebar.title("Login")
    password = st.sidebar.text_input("Enter password:", type="password")
    if password == PASSWORD:
        st.sidebar.success("Password correct!")
        return True
    elif password:  # Show an error message only if some input is provided
        st.sidebar.error("Incorrect password")
    return False

# Main app logic
if login():  # 로그인 함수 호출 및 성공 시만 진행

    # Track the uploaded file in session state to reset the UI when a new file is uploaded
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

    # 1. 파일 업로드
    st.markdown("<h4 style='color:grey;'>데이터 업로드</h4>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("하나의 판독문 열로 구성된 파일을 올려주세요.", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Reset session state when a new file is uploaded
        if st.session_state.uploaded_file != uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.phrases_by_code = {}
            st.session_state.text_input = ""
            st.session_state.code_input = ""
            st.session_state.coded_df = None  # Initialize session state for coded DataFrame

        try:
            # 파일 타입에 따라 데이터 읽기
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)

            # 데이터 미리보기 표시
            st.divider()
            st.markdown("<h4 style='color:grey;'>데이터 미리보기</h4>", unsafe_allow_html=True)
            st.dataframe(df)

            # 'coding' 열 추가
            if 'coding' not in df.columns:
                df['coding'] = np.nan  # 기본적으로 nan으로 채움

            # Store df in session state
            st.session_state.df = df  # Ensure df is stored initially

        except Exception as e:
            st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        
        # Session state initialization for phrases (reset on new file upload)
        if 'phrases_by_code' not in st.session_state:
            st.session_state.phrases_by_code = {}  # Session state to hold phrases and codes

        # 2. 코드를 입력 후 텍스트 입력 구조
        st.divider()
        st.markdown("<h4 style='color:grey;'>코드 & 텍스트 입력창</h4>", unsafe_allow_html=True)
        flexible_callout(
            """
            하단에 코드와 함께 텍스트를 입력 시, 해당 텍스트가 포함된 판독문 행은 함께 입력된 코드로 코딩이 이뤄집니다. 
            
            주의!) 먼저 입력한 코드 내용보다 뒤에 입력한 코드 내용에 높은 우선순위가 부여됩니다.
                - Case 1) 코드 1과 "disease1" 입력 후, 코드 2과 다시 "disease1" 입력: "disease1"이 포함된 행은 2로 코딩됩니다.
                - Case 2) 코드 1과 "disease1" 입력 후, 코드 2과 "disease2" 입력: "disease1, disease2" 모두 포함된 행은 2로 코딩됩니다.""",
            background_color="#D9D9D9",font_color="#000000",font_size=12,alignment="left",line_height=1.4)


        current_code = st.text_input("코드를 입력하고 엔터를 누르세요. (ex - 0, 1, 2)", key="code_input")

        if current_code:
            current_code = int(current_code)  # Convert to integer code

            # Check if current code already exists in session state
            if current_code not in st.session_state.phrases_by_code:
                st.session_state.phrases_by_code[current_code] = []  # Create a new list for this code if doesn't exist

            # Define a callback function to handle text input
            def add_text():
                if st.session_state.text_input:
                    st.session_state.phrases_by_code[current_code].append(st.session_state.text_input)
                    st.session_state.text_input = ""  # Reset the input field
            
            # Allow multiple text input with callback
            st.text_input("텍스트를 입력하고 엔터를 누르세요.", key="text_input", on_change=add_text)
        
        # 4. 입력된 코딩 및 텍스트 목록 표시 및 삭제 기능 추가
        if st.session_state.phrases_by_code:
            st.write("")
            st.markdown("<h5>현재 입력된 코드 및 텍스트 목록 :</h5>", unsafe_allow_html=True)
            for code, phrases in st.session_state.phrases_by_code.items():
                st.markdown(f"<span style='color:red;'>코드 {code}에 대한 텍스트:</span>", unsafe_allow_html=True)
                # Create a dynamic list where phrases can be deleted
                for phrase in phrases:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"<span style='color:red;'>- {phrase}</span>", unsafe_allow_html=True)
                    with col2:
                        if st.button(f"삭제", key=f"delete_{code}_{phrase}"):
                            st.session_state.phrases_by_code[code].remove(phrase)  # Remove the phrase from the list
                            # Force rerun by altering a session state value
                            st.session_state["rerun_trigger"] = not st.session_state.get("rerun_trigger", False)

        # 5. 미처리 항목을 자동으로 0으로 처리 또는 다른 방식 처리
        st.divider()
        st.markdown("<h4 style='color:grey;'>코딩되지 않은 그 외 판독문 처리 방법</h4>", unsafe_allow_html=True)

        # Use radio buttons to select between filling with 0 or missing
        fill_option = st.radio("처리 방법을 선택하세요.", ("전부 0으로", "전부 missing으로"))

        # 3. 완료 버튼 - 텍스트 입력 후 활성화
        st.divider()
        st.markdown("<h4 style='color:grey;'>코딩 작업 종료하기</h4>", unsafe_allow_html=True)
        if current_code and st.session_state.phrases_by_code[current_code]:
            if st.button("코딩 종료"):
                # Create a temporary lowercase column for matching
                df = st.session_state.df.copy()  # Use session_state to preserve df between runs
                df['lower_temp'] = df.iloc[:, 0].str.lower()

                # Process the text for each code
                for code, phrases in st.session_state.phrases_by_code.items():
                    for phrase in phrases:
                        # Match against the lowercase temporary column
                        df['coding'] = df['coding'].where(~df['lower_temp'].str.contains(phrase.lower(), na=False), code)

                # Apply the appropriate fill method based on the radio selection
                if fill_option == "전부 0으로":
                    df['coding'].fillna(0, inplace=True)
                elif fill_option == "전부 missing으로":
                    df['coding'].fillna(np.nan, inplace=True)
                
                # Drop the temporary column after coding
                df.drop(columns=['lower_temp'], inplace=True)

                # Store the coded DataFrame in session state
                st.session_state.coded_df = df

                # Display coding result
                st.write("코딩이 완료되었습니다.")
                st.dataframe(st.session_state.coded_df)

            # 6. 데이터 다운로드 버튼 (Excel 또는 CSV)
            if st.session_state.coded_df is not None:
                st.divider()
                st.markdown("<h4 style='color:grey;'>데이터 다운로드</h4>", unsafe_allow_html=True)
                export_format = st.radio("파일 형식을 선택하세요", options=["CSV", "Excel"])
                if export_format == "CSV":
                    csv = st.session_state.coded_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="CSV 다운로드",
                        data=csv,
                        file_name="coded_data.csv",
                        mime='text/csv'
                    )
                elif export_format == "Excel":
                    buffer = BytesIO()
                    try:
                        # Use ExcelWriter with openpyxl
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            st.session_state.coded_df.to_excel(writer, index=False)
                        
                        # Move the buffer's position back to the start
                        buffer.seek(0)
                        
                        # Offer the download button for Excel
                        st.download_button(
                            label="Excel 다운로드",
                            data=buffer,
                            file_name="coded_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    finally:
                        buffer.close()  # Ensure buffer is properly closed
else:
    st.markdown("<h4 style='color:grey;'>시스템 접근을 위해 로그인이 필요합니다.</h4>", unsafe_allow_html=True)
